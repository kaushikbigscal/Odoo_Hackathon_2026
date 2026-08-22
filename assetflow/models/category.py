# -*- coding: utf-8 -*-
from odoo import fields, models


class AssetflowCategory(models.Model):
    _name = "assetflow.category"
    _description = "Asset Category"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    warranty_period_months = fields.Integer(string="Warranty Period (Months)", help="Category-specific warranty in months")
    active = fields.Boolean(default=True)
    asset_ids = fields.One2many("assetflow.asset", "category_id", string="Assets")
    asset_count = fields.Integer(compute="_compute_asset_count")

    def _compute_asset_count(self):
        for cat in self:
            cat.asset_count = len(cat.asset_ids)
