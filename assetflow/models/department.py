# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssetflowDepartment(models.Model):
    _name = "assetflow.department"
    _description = "Department"
    _order = "name"
    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char(required=True)
    code = fields.Char()
    head_id = fields.Many2one("res.users", string="Department Head")
    parent_id = fields.Many2one("assetflow.department", string="Parent Department", index=True, ondelete="cascade")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many("assetflow.department", "parent_id", string="Sub-Departments")
    employee_ids = fields.One2many("assetflow.employee", "department_id", string="Employees")
    employee_count = fields.Integer(compute="_compute_employee_count", string="Employees #")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Department code must be unique."),
    ]

    @api.depends("employee_ids")
    def _compute_employee_count(self):
        for dept in self:
            dept.employee_count = len(dept.employee_ids)

    @api.constrains("parent_id")
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create a recursive department hierarchy."))