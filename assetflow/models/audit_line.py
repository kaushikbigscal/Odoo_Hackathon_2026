# -*- coding: utf-8 -*-
from odoo import fields, models


class AssetflowAuditLine(models.Model):
    _name = "assetflow.audit.line"
    _description = "Audit Line"
    _order = "asset_id"

    audit_cycle_id = fields.Many2one("assetflow.audit.cycle", string="Audit Cycle", required=True, ondelete="cascade")
    asset_id = fields.Many2one("assetflow.asset", string="Asset", required=True)
    status = fields.Selection([
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("missing", "Missing"),
        ("damaged", "Damaged"),
    ], default="pending", copy=False)
    notes = fields.Text()
    auditor_id = fields.Many2one("assetflow.employee", string="Auditor")
