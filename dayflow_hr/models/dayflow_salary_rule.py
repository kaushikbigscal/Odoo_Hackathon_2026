from odoo import fields, models


class DayflowSalaryRule(models.Model):
    _name = "dayflow.salary.rule"
    _description = "Dayflow Salary Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    rule_type = fields.Selection([
        ("allowance", "Allowance"),
        ("deduction", "Deduction"),
    ], required=True, default="allowance")
    amount_type = fields.Selection([
        ("fixed", "Fixed Amount"),
        ("percentage_basic", "Percentage of Basic Wage"),
    ], required=True, default="percentage_basic")
    amount_value = fields.Float(
        required=True,
        help="Fixed amount, or percentage of basic wage (e.g. 12 for 12%), depending on Amount Type.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("dayflow_salary_rule_code_unique", "unique(code)", "Salary rule code must be unique."),
    ]

    def _dayflow_compute_amount(self, basic_wage):
        self.ensure_one()
        if self.amount_type == "fixed":
            return self.amount_value
        return basic_wage * self.amount_value / 100.0
