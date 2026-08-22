import logging
import secrets

from odoo import api, fields, models, _
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    dayflow_employee_code = fields.Char(string="Employee ID", copy=False)
    dayflow_requested_role = fields.Selection([
        ("employee", "Employee"),
        ("hr", "HR / Admin"),
    ], string="Requested Role", default="employee", copy=False)
    dayflow_role_status = fields.Selection([
        ("none", "No Request"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], string="Role Request Status", default="none", copy=False)
    dayflow_email_verified = fields.Boolean(string="Email Verified", default=False, copy=False)
    dayflow_verification_token = fields.Char(copy=False)

    @api.model
    def _signup_create_user(self, values):
        employee_code = values.pop("dayflow_employee_code", None)
        requested_role = values.pop("dayflow_requested_role", "employee") or "employee"
        user = super()._signup_create_user(values)
        if employee_code:
            user._dayflow_setup_after_signup(employee_code, requested_role)
        return user

    def _dayflow_setup_after_signup(self, employee_code, requested_role):
        self.ensure_one()
        internal_group = self.env.ref("base.group_user")
        portal_group = self.env.ref("base.group_portal", raise_if_not_found=False)
        group_commands = [(4, internal_group.id)]
        if portal_group:
            group_commands.append((3, portal_group.id))

        role_status = "pending" if requested_role == "hr" else "none"
        token = secrets.token_urlsafe(32)
        dashboard_action = self.env.ref("dayflow_hr.action_dayflow_dashboard", raise_if_not_found=False)

        self.write({
            "groups_id": group_commands,
            "dayflow_employee_code": employee_code,
            "dayflow_requested_role": requested_role,
            "dayflow_role_status": role_status,
            "dayflow_email_verified": False,
            "dayflow_verification_token": token,
            "action_id": dashboard_action.id if dashboard_action else False,
        })
        self.sudo()._dayflow_link_employee(employee_code)
        self.sudo()._dayflow_send_verification_email()
        # Deactivate last: the signup controller expects the AccessDenied this
        # triggers on the immediate post-signup login attempt and turns it
        # into a "check your email" message instead of a hard error.
        self.write({"active": False})

    def _dayflow_link_employee(self, employee_code):
        self.ensure_one()
        employee_model = self.env["hr.employee"]
        employee = employee_model.search([
            ("dayflow_employee_code", "=", employee_code),
            ("user_id", "=", False),
        ], limit=1)
        if employee:
            employee.write({"user_id": self.id, "work_email": self.email})
        else:
            employee_model.create({
                "name": self.name,
                "work_email": self.email,
                "user_id": self.id,
                "dayflow_employee_code": employee_code,
            })

    def _dayflow_send_verification_email(self):
        self.ensure_one()
        template = self.env.ref("dayflow_hr.mail_template_email_verification", raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True, email_values={"email_to": self.email})
        else:
            _logger.warning("Dayflow HR: verification email template missing, skipped sending to %s", self.email)

    @api.model
    def action_dayflow_verify_email(self, token):
        user = self.sudo().with_context(active_test=False).search([
            ("dayflow_verification_token", "=", token),
            ("dayflow_email_verified", "=", False),
        ], limit=1)
        if not user:
            return False
        user.write({
            "active": True,
            "dayflow_email_verified": True,
            "dayflow_verification_token": False,
        })
        return True

    def _dayflow_admin_group_xmlids(self):
        # Dayflow's "HR / Admin" role spans employee records, attendance and
        # leave approvals, so approving it grants the officer/manager group
        # from each of those stock HR apps, not just hr.group_hr_user.
        return [
            "hr.group_hr_user",
            "hr_holidays.group_hr_holidays_manager",
            "hr_attendance.group_hr_attendance_manager",
        ]

    def action_dayflow_approve_role_request(self):
        if not self.env.user.has_group("hr.group_hr_manager"):
            raise AccessError(_("Only an HR Administrator can approve role requests."))
        group_ids = [self.env.ref(xmlid).id for xmlid in self._dayflow_admin_group_xmlids()]
        for user in self:
            if user.dayflow_role_status != "pending":
                continue
            user.sudo().write({
                "dayflow_role_status": "approved",
                "groups_id": [(4, gid) for gid in group_ids],
            })
            user.sudo()._dayflow_notify_role_decision(approved=True)

    def action_dayflow_reject_role_request(self):
        if not self.env.user.has_group("hr.group_hr_manager"):
            raise AccessError(_("Only an HR Administrator can reject role requests."))
        for user in self.filtered(lambda u: u.dayflow_role_status == "pending"):
            user.sudo().dayflow_role_status = "rejected"
            user.sudo()._dayflow_notify_role_decision(approved=False)

    def _dayflow_notify_role_decision(self, approved):
        self.ensure_one()
        template_xmlid = (
            "dayflow_hr.mail_template_role_approved" if approved
            else "dayflow_hr.mail_template_role_rejected"
        )
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True, email_values={"email_to": self.email})
