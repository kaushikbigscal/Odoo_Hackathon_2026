from odoo import fields, models


class DayflowPayslipLine(models.Model):
    _name = "dayflow.payslip.line"
    _description = "Dayflow Payslip Line"
    _order = "sequence, id"

    payslip_id = fields.Many2one("dayflow.payslip", required=True, ondelete="cascade")
    rule_id = fields.Many2one("dayflow.salary.rule")
    sequence = fields.Integer(related="rule_id.sequence", store=True)
    name = fields.Char(required=True)
    rule_type = fields.Selection([
        ("allowance", "Allowance"),
        ("deduction", "Deduction"),
    ], required=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(related="payslip_id.currency_id")
