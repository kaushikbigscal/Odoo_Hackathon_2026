# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetflowAsset(models.Model):
    _name = "assetflow.asset"
    _description = "Asset"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    category_id = fields.Many2one("assetflow.category", string="Category", required=True, tracking=True)
    asset_tag = fields.Char(string="Asset Tag", readonly=True, copy=False, tracking=True)
    serial_number = fields.Char(string="Serial Number", copy=False)
    acquisition_date = fields.Date(string="Acquisition Date")
    acquisition_cost = fields.Float(string="Acquisition Cost")
    condition = fields.Selection([
        ("new", "New"),
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
    ], default="new", tracking=True)
    location = fields.Char(string="Location")
    photo = fields.Binary(string="Photo")
    is_bookable = fields.Boolean(string="Shared / Bookable", default=False)
    department_id = fields.Many2one("assetflow.department", string="Department")
    state = fields.Selection([
        ("available", "Available"),
        ("allocated", "Allocated"),
        ("reserved", "Reserved"),
        ("under_maintenance", "Under Maintenance"),
        ("lost", "Lost"),
        ("retired", "Retired"),
        ("disposed", "Disposed"),
    ], default="available", required=True, tracking=True, copy=False)
    active = fields.Boolean(default=True)

    allocation_ids = fields.One2many("assetflow.allocation", "asset_id", string="Allocations")
    booking_ids = fields.One2many("assetflow.booking", "asset_id", string="Bookings")
    maintenance_request_ids = fields.One2many("assetflow.maintenance.request", "asset_id", string="Maintenance Requests")

    current_allocation_id = fields.Many2one("assetflow.allocation", string="Current Allocation",
                                             compute="_compute_current_allocation", store=True)
    allocation_count = fields.Integer(compute="_compute_counts")
    maintenance_count = fields.Integer(compute="_compute_counts")

    _sql_constraints = [
        ("asset_tag_uniq", "unique(asset_tag)", "Asset tag must be unique!"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("asset_tag"):
                vals["asset_tag"] = self.env["ir.sequence"].next_by_code("assetflow.asset") or "AF-NEW"
        return super().create(vals_list)

    @api.depends("allocation_ids", "allocation_ids.state")
    def _compute_current_allocation(self):
        for asset in self:
            alloc = asset.allocation_ids.filtered(lambda a: a.state == "active")
            asset.current_allocation_id = alloc[0] if alloc else False

    def _compute_counts(self):
        for asset in self:
            asset.allocation_count = len(asset.allocation_ids)
            asset.maintenance_count = len(asset.maintenance_request_ids)

    def action_allocate(self):
        self.ensure_one()
        if self.state not in ("available",):
            raise UserError(_("Only available assets can be allocated."))
        return {
            "type": "ir.actions.act_window",
            "name": "Allocate Asset",
            "res_model": "assetflow.allocation",
            "view_mode": "form",
            "context": {"default_asset_id": self.id, "default_state": "requested"},
            "target": "new",
        }

    def action_view_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Allocation History",
            "res_model": "assetflow.allocation",
            "view_mode": "list,form",
            "domain": [("asset_id", "=", self.id)],
        }
