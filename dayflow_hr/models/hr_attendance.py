from odoo import models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _dayflow_touch_days(self):
        day_model = self.env["dayflow.attendance.day"]
        for attendance in self:
            if not attendance.check_in:
                continue
            check_in_date = attendance.check_in.date()
            check_out_date = attendance.check_out.date() if attendance.check_out else check_in_date
            day_model._dayflow_recompute(attendance.employee_id, check_in_date, check_out_date)

    def create(self, vals_list):
        records = super().create(vals_list)
        records._dayflow_touch_days()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {"check_in", "check_out", "employee_id"} & vals.keys():
            self._dayflow_touch_days()
        return res
