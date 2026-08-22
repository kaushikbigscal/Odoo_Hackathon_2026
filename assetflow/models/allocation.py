# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetflowAllocation(models.Model):
    _name = "assetflow.allocation"
    _description = "Asset Allocation"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(string="Reference", copy=False, readonly=True, default=lambda self: _("New"))
    asset_id = fields.Many2one("assetflow.asset", string="Asset", required=True, tracking=True)
    employee_id = fields.Many2one("assetflow.employee", string="Allocated To", tracking=True)
    department_id = fields.Many2one("assetflow.department", string="Department", tracking=True)
    expected_return_date = fields.Date(string="Expected Return Date")
    actual_return_date = fields.Date(string="Actual Return Date", readonly=True)
    condition_checkin = fields.Text(string="Condition Check-in Notes")
    state = fields.Selection([
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("active", "Active"),
        ("return_requested", "Return Requested"),
        ("returned", "Returned"),
        ("rejected", "Rejected"),
    ], default="requested", tracking=True, copy=False)
    is_overdue = fields.Boolean(compute="_compute_is_overdue", store=True)

    @api.depends("expected_return_date", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for alloc in self:
            alloc.is_overdue = bool(
                alloc.expected_return_date and alloc.expected_return_date < today
                and alloc.state == "active"
            )

    @api.constrains("asset_id", "state")
    def _check_no_double_allocation(self):
        for alloc in self:
            if alloc.state == "active":
                existing = self.search([
                    ("asset_id", "=", alloc.asset_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", alloc.id),
                ])
                if existing:
                    raise UserError(_(
                        "Asset %s is already allocated to %s.",
                        alloc.asset_id.name, existing.employee_id.name
                    ))

    def action_approve(self):
        for alloc in self:
            alloc.write({"state": "approved"})
            alloc.asset_id.write({"state": "allocated"})

    def action_activate(self):
        for alloc in self:
            alloc.write({"state": "active"})
            alloc.asset_id.write({"state": "allocated"})

    def action_return(self):
        for alloc in self:
            alloc.write({"state": "returned", "actual_return_date": fields.Date.context_today(self)})
            alloc.asset_id.write({"state": "available"})

    def action_reject(self):
        for alloc in self:
            alloc.write({"state": "rejected"})

    def _flag_overdue_allocations(self):
        today = fields.Date.context_today(self)
        overdue = self.search([
            ("expected_return_date", "<", today),
            ("state", "=", "active"),
        ])
        for alloc in overdue:
            alloc.message_post(body="This allocation is overdue! Please arrange return.")
