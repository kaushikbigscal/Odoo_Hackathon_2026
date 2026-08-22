# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AssetflowTransfer(models.Model):
    _name = "assetflow.transfer"
    _description = "Asset Transfer"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(string="Reference", copy=False, readonly=True, default=lambda self: _("New"))
    asset_id = fields.Many2one("assetflow.asset", string="Asset", required=True, tracking=True)
    from_employee_id = fields.Many2one("assetflow.employee", string="From", readonly=True)
    to_employee_id = fields.Many2one("assetflow.employee", string="To", required=True, tracking=True)
    reason = fields.Text(string="Reason")
    state = fields.Selection([
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    ], default="requested", tracking=True, copy=False)

    def action_approve(self):
        for t in self:
            t.write({"state": "approved"})
            old_alloc = t.asset_id.allocation_ids.filtered(lambda a: a.state == "active")
            if old_alloc:
                old_alloc[0].write({"state": "returned", "actual_return_date": fields.Date.context_today(self)})
            t.asset_id.write({"state": "allocated"})
            self.env["assetflow.allocation"].create({
                "asset_id": t.asset_id.id,
                "employee_id": t.to_employee_id.id,
                "state": "active",
            })

    def action_complete(self):
        for t in self:
            t.write({"state": "completed"})

    def action_reject(self):
        for t in self:
            t.write({"state": "rejected"})
