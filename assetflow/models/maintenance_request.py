# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AssetflowMaintenanceRequest(models.Model):
    _name = "assetflow.maintenance.request"
    _description = "Maintenance Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Request Title", required=True, tracking=True)
    asset_id = fields.Many2one("assetflow.asset", string="Asset", required=True, tracking=True)
    requester_id = fields.Many2one("assetflow.employee", string="Requested By", required=True, tracking=True)
    description = fields.Text(string="Issue Description")
    priority = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ], default="medium", required=True, tracking=True)
    photo = fields.Binary(string="Photo")
    technician_id = fields.Char(string="Assigned Technician")
    state = fields.Selection([
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("technician_assigned", "Technician Assigned"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ], default="pending", tracking=True, copy=False)

    def action_approve(self):
        for r in self:
            r.write({"state": "approved"})
            r.asset_id.write({"state": "under_maintenance"})

    def action_reject(self):
        for r in self:
            r.write({"state": "rejected"})

    def action_assign_technician(self):
        for r in self:
            r.write({"state": "technician_assigned"})

    def action_start(self):
        for r in self:
            r.write({"state": "in_progress"})

    def action_resolve(self):
        for r in self:
            r.write({"state": "resolved"})
            if r.asset_id.state == "under_maintenance":
                r.asset_id.write({"state": "available"})
