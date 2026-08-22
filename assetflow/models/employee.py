# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AssetflowEmployee(models.Model):
    _name = "assetflow.employee"
    _description = "Employee"
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    user_id = fields.Many2one("res.users", string="Related User", ondelete="set null")
    department_id = fields.Many2one("assetflow.department", string="Department")
    role = fields.Selection([
        ("employee", "Employee"),
        ("department_head", "Department Head"),
        ("asset_manager", "Asset Manager"),
    ], default="employee", required=True, tracking=True)
    status = fields.Selection([
        ("active", "Active"),
        ("inactive", "Inactive"),
    ], default="active", tracking=True)

    allocated_asset_ids = fields.One2many("assetflow.allocation", "employee_id", string="Allocated Assets")
    booking_ids = fields.One2many("assetflow.booking", "employee_id", string="Bookings")
    maintenance_request_ids = fields.One2many("assetflow.maintenance.request", "requester_id", string="Maintenance Requests")
    allocation_count = fields.Integer(compute="_compute_counts")
    booking_count = fields.Integer(compute="_compute_counts")

    def _compute_counts(self):
        for emp in self:
            emp.allocation_count = len(emp.allocated_asset_ids)
            emp.booking_count = len(emp.booking_ids)

    def action_view_assets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "My Assets",
            "res_model": "assetflow.allocation",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
        }
