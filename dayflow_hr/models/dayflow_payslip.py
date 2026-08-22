from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DayflowPayslip(models.Model):
    _name = "dayflow.payslip"
    _description = "Dayflow Payslip"
    _order = "date_from desc, id desc"
    _inherit = ["mail.thread"]

    employee_id = fields.Many2one("hr.employee", required=True, tracking=True)
    contract_id = fields.Many2one("hr.contract", compute="_compute_contract_id", store=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    date_from = fields.Date(required=True, tracking=True)
    date_to = fields.Date(required=True, tracking=True)
    name = fields.Char(compute="_compute_name", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_contract_id", store=True)

    expected_days = fields.Integer(readonly=True, help="Scheduled working days in the period.")
    absent_days = fields.Integer(readonly=True)
    worked_days = fields.Integer(readonly=True)

    basic_wage = fields.Monetary(readonly=True, help="Contract wage prorated for unpaid absences in the period.")
    line_ids = fields.One2many("dayflow.payslip.line", "payslip_id", copy=True)
    gross_pay = fields.Monetary(compute="_compute_totals", store=True)
    total_deductions = fields.Monetary(compute="_compute_totals", store=True)
    net_pay = fields.Monetary(compute="_compute_totals", store=True)

    state = fields.Selection([
        ("draft", "Draft"),
        ("computed", "Computed"),
        ("confirmed", "Confirmed"),
        ("paid", "Paid"),
        ("cancel", "Cancelled"),
    ], default="draft", required=True, tracking=True)

    _sql_constraints = [
        ("dayflow_payslip_period_check", "CHECK(date_to >= date_from)",
         "The period end date must be on or after its start date."),
    ]

    @api.depends("employee_id")
    def _compute_contract_id(self):
        for slip in self:
            contract = slip.employee_id.sudo().contract_id
            slip.contract_id = contract
            slip.currency_id = contract.currency_id if contract else slip.employee_id.company_id.currency_id

    @api.depends("employee_id", "date_from")
    def _compute_name(self):
        for slip in self:
            if slip.employee_id and slip.date_from:
                slip.name = "%s - %s" % (slip.employee_id.name, slip.date_from.strftime("%B %Y"))
            else:
                slip.name = _("Payslip")

    @api.depends("line_ids.amount", "line_ids.rule_type", "basic_wage")
    def _compute_totals(self):
        for slip in self:
            allowances = sum(slip.line_ids.filtered(lambda l: l.rule_type == "allowance").mapped("amount"))
            deductions = sum(slip.line_ids.filtered(lambda l: l.rule_type == "deduction").mapped("amount"))
            slip.gross_pay = slip.basic_wage + allowances
            slip.total_deductions = deductions
            slip.net_pay = slip.gross_pay - deductions

    def action_compute(self):
        for slip in self:
            if slip.state not in ("draft", "computed"):
                raise UserError(_("Only draft or computed payslips can be (re)computed."))
            slip._dayflow_compute_worked_days()
            slip._dayflow_generate_lines()
            slip.state = "computed"

    def _dayflow_compute_worked_days(self):
        self.ensure_one()
        # hr.contract is gated by its own group (hr_contract.group_hr_contract_manager),
        # separate from hr.group_hr_user/hr_holidays/hr_attendance, so reading it here
        # must not depend on the caller also holding that specific group.
        contract = self.sudo().contract_id
        if not contract:
            raise UserError(_("%s has no contract; set one before computing a payslip.") % self.employee_id.name)
        days = self.env["dayflow.attendance.day"].search([
            ("employee_id", "=", self.employee_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ])
        expected = len(days)
        absent = len(days.filtered(lambda d: d.status == "absent"))
        worked = expected - absent
        proration = (worked / expected) if expected else 1.0
        self.expected_days = expected
        self.absent_days = absent
        self.worked_days = worked
        self.basic_wage = round(contract.wage * proration, 2)

    def _dayflow_generate_lines(self):
        self.ensure_one()
        self.line_ids.unlink()
        rules = self.env["dayflow.salary.rule"].search([("active", "=", True)])
        lines = []
        for rule in rules:
            amount = rule._dayflow_compute_amount(self.basic_wage)
            lines.append((0, 0, {
                "rule_id": rule.id,
                "name": rule.name,
                "rule_type": rule.rule_type,
                "amount": round(amount, 2),
            }))
        self.line_ids = lines

    def action_confirm(self):
        for slip in self:
            if slip.state != "computed":
                raise UserError(_("Compute the payslip before confirming it."))
            slip.state = "confirmed"
            slip._dayflow_notify_employee("dayflow_hr.mail_template_payslip_confirmed")

    def action_mark_paid(self):
        for slip in self:
            if slip.state != "confirmed":
                raise UserError(_("Only confirmed payslips can be marked as paid."))
            slip.state = "paid"
            slip._dayflow_notify_employee("dayflow_hr.mail_template_payslip_paid")

    def action_reset_draft(self):
        for slip in self.filtered(lambda s: s.state != "paid"):
            slip.state = "draft"

    def _dayflow_notify_employee(self, template_xmlid):
        self.ensure_one()
        email = self.employee_id.work_email or self.employee_id.user_id.email
        if not email:
            return
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True, email_values={"email_to": email})
