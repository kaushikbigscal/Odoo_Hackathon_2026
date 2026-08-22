from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def create(self, vals_list):
        records = super().create(vals_list)
        # New requests start directly in "confirm" (no draft step in this
        # version of hr_holidays), so the submission notice has to fire here
        # rather than in write() below.
        for leave in records:
            if leave.state == "confirm":
                leave._dayflow_notify_approvers()
        return records

    def write(self, vals):
        old_states = {leave.id: leave.state for leave in self} if "state" in vals else {}
        res = super().write(vals)
        if "state" in vals:
            day_model = self.env["dayflow.attendance.day"]
            for leave in self:
                if leave.date_from and leave.date_to:
                    day_model._dayflow_recompute(leave.employee_id, leave.date_from.date(), leave.date_to.date())
                leave._dayflow_notify_state_change(old_states.get(leave.id))
        return res

    def _dayflow_notify_state_change(self, old_state):
        self.ensure_one()
        if self.state == old_state:
            return
        if self.state == "confirm":
            self._dayflow_notify_approvers()
        elif self.state == "validate":
            self._dayflow_notify_employee("dayflow_hr.mail_template_leave_approved")
        elif self.state == "refuse":
            self._dayflow_notify_employee("dayflow_hr.mail_template_leave_refused")

    def _dayflow_notify_approvers(self):
        self.ensure_one()
        approvers = self.sudo()._get_responsible_for_approval()
        emails = [email for email in approvers.mapped("email") if email]
        if not emails:
            return
        template = self.env.ref("dayflow_hr.mail_template_leave_submitted", raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True, email_values={"email_to": ",".join(emails)})

    def _dayflow_notify_employee(self, template_xmlid):
        self.ensure_one()
        email = self.employee_id.work_email or self.employee_id.user_id.email
        if not email:
            return
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True, email_values={"email_to": email})
