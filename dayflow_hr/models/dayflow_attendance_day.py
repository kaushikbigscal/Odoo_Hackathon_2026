from datetime import datetime, timedelta

from odoo import fields, models


class DayflowAttendanceDay(models.Model):
    _name = "dayflow.attendance.day"
    _description = "Dayflow Daily Attendance Status"
    _order = "date desc, employee_id"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    date = fields.Date(required=True, index=True)
    status = fields.Selection([
        ("present", "Present"),
        ("half_day", "Half-day"),
        ("absent", "Absent"),
        ("leave", "Leave"),
    ], required=True)
    worked_hours = fields.Float(string="Worked Hours")
    expected_hours = fields.Float(string="Expected Hours")
    check_in = fields.Datetime()
    check_out = fields.Datetime()

    _sql_constraints = [
        ("dayflow_attendance_day_unique", "unique(employee_id, date)",
         "Only one attendance-day record per employee per day."),
    ]

    _HALF_DAY_RATIO = 0.5

    def _dayflow_expected_hours(self, employee, date):
        calendar = employee.resource_calendar_id
        if not calendar:
            return 0.0
        dayofweek = str(date.weekday())
        attendances = calendar.attendance_ids.filtered(
            lambda a: a.dayofweek == dayofweek and a.day_period != "lunch"
        )
        return sum(a.hour_to - a.hour_from for a in attendances)

    def _dayflow_recompute(self, employees, date_from, date_to):
        """(Re)compute the daily attendance status for ``employees`` between
        ``date_from`` and ``date_to`` (inclusive) and upsert the matching
        dayflow.attendance.day rows. Days the employee isn't scheduled to
        work (per their resource calendar) are skipped entirely."""
        employees = employees.filtered("active")
        if not employees or date_from > date_to:
            return

        range_start = datetime.combine(date_from, datetime.min.time())
        range_end = datetime.combine(date_to + timedelta(days=1), datetime.min.time())

        attendances = self.env["hr.attendance"].search([
            ("employee_id", "in", employees.ids),
            ("check_in", "<", range_end),
            "|", ("check_out", "=", False), ("check_out", ">=", range_start),
        ])
        leaves = self.env["hr.leave"].search([
            ("employee_id", "in", employees.ids),
            ("state", "=", "validate"),
            ("date_from", "<", range_end),
            ("date_to", ">=", range_start),
        ])
        existing = self.search([
            ("employee_id", "in", employees.ids),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ])
        existing_by_key = {(rec.employee_id.id, rec.date): rec for rec in existing}
        today = fields.Date.context_today(self)

        to_create = []
        for employee in employees:
            emp_attendances = attendances.filtered(lambda a: a.employee_id == employee)
            emp_leaves = leaves.filtered(lambda l: l.employee_id == employee)
            date = date_from
            while date <= date_to:
                expected_hours = self._dayflow_expected_hours(employee, date)
                if not expected_hours:
                    date += timedelta(days=1)
                    continue  # not a scheduled working day (e.g. weekend)

                day_start = datetime.combine(date, datetime.min.time())
                day_end = day_start + timedelta(days=1)

                on_leave = any(leave.date_from < day_end and leave.date_to >= day_start for leave in emp_leaves)
                day_attendances = emp_attendances.filtered(
                    lambda a: day_start <= a.check_in < day_end
                )
                worked_hours = sum(day_attendances.mapped("worked_hours"))
                check_in = min(day_attendances.mapped("check_in")) if day_attendances else False
                closed = day_attendances.filtered("check_out")
                check_out = max(closed.mapped("check_out")) if closed else False

                if on_leave:
                    status = "leave"
                elif worked_hours >= expected_hours * self._HALF_DAY_RATIO:
                    status = "present"
                elif worked_hours > 0:
                    status = "half_day"
                elif date < today:
                    status = "absent"
                else:
                    # today or future with nothing recorded yet: too early to call
                    date += timedelta(days=1)
                    continue

                vals = {
                    "status": status,
                    "worked_hours": worked_hours,
                    "expected_hours": expected_hours,
                    "check_in": check_in,
                    "check_out": check_out,
                }
                key = (employee.id, date)
                if key in existing_by_key:
                    existing_by_key[key].write(vals)
                else:
                    to_create.append({"employee_id": employee.id, "date": date, **vals})

                date += timedelta(days=1)

        if to_create:
            self.create(to_create)

    def _dayflow_cron_recompute_recent(self):
        today = fields.Date.context_today(self)
        employees = self.env["hr.employee"].search([])
        self._dayflow_recompute(employees, today - timedelta(days=2), today)
