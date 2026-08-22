# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AssetflowAuditCycle(models.Model):
    _name = "assetflow.audit.cycle"
    _description = "Asset Audit Cycle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Audit Cycle", required=True, tracking=True)
    department_id = fields.Many2one("assetflow.department", string="Department")
    location = fields.Char(string="Location")
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    auditor_ids = fields.Many2many("assetflow.employee", string="Auditors")
    line_ids = fields.One2many("assetflow.audit.line", "audit_cycle_id", string="Audit Lines")
    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("closed", "Closed"),
    ], default="draft", tracking=True, copy=False)

    discrepancy_count = fields.Integer(compute="_compute_discrepancy_count")

    def _compute_discrepancy_count(self):
        for cycle in self:
            cycle.discrepancy_count = len(
                cycle.line_ids.filtered(lambda l: l.status in ("missing", "damaged"))
            )

    def action_generate_lines(self):
        for cycle in self:
            domain = []
            if cycle.department_id:
                domain.append(("department_id", "=", cycle.department_id.id))
            if cycle.location:
                domain.append(("location", "=", cycle.location))
            assets = self.env["assetflow.asset"].search(domain)
            lines = [(0, 0, {
                "asset_id": asset.id,
                "auditor_id": cycle.auditor_ids[0].id if cycle.auditor_ids else False,
            }) for asset in assets]
            cycle.write({"line_ids": lines, "state": "in_progress"})

    def action_close(self):
        for cycle in self:
            for line in cycle.line_ids.filtered(lambda l: l.status == "missing"):
                line.asset_id.write({"state": "lost"})
            cycle.write({"state": "closed"})
