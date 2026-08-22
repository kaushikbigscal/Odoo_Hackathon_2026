from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    dayflow_employee_code = fields.Char(string="Employee ID", copy=False, index=True)

    # hr_contract's contract_id/wage are restricted to hr.group_hr_user, so a
    # plain employee can never see their own salary through those fields even
    # once they can read their own hr.employee record. This mirrors just the
    # current wage through a field with no such restriction.
    dayflow_current_wage = fields.Monetary(
        string="Current Wage",
        compute="_compute_dayflow_current_wage",
        currency_field="dayflow_wage_currency_id",
    )
    dayflow_wage_currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_dayflow_current_wage",
    )

    @api.depends("contract_id", "contract_id.wage", "contract_id.currency_id")
    def _compute_dayflow_current_wage(self):
        for employee in self:
            contract = employee.sudo().contract_id
            employee.dayflow_current_wage = contract.wage if contract else 0.0
            employee.dayflow_wage_currency_id = (
                contract.currency_id if contract else employee.sudo().company_id.currency_id
            )
