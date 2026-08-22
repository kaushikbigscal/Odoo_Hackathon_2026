# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetflowBooking(models.Model):
    _name = "assetflow.booking"
    _description = "Resource Booking"
    _inherit = ["mail.thread"]
    _order = "start_datetime desc"

    name = fields.Char(string="Booking Title", required=True, tracking=True)
    asset_id = fields.Many2one("assetflow.asset", string="Resource", required=True, tracking=True,
                                domain=[("is_bookable", "=", True)])
    employee_id = fields.Many2one("assetflow.employee", string="Booked By", required=True, tracking=True)
    start_datetime = fields.Datetime(string="Start", required=True)
    end_datetime = fields.Datetime(string="End", required=True)
    state = fields.Selection([
        ("upcoming", "Upcoming"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], default="upcoming", tracking=True, copy=False)
    notes = fields.Text()

    @api.constrains("asset_id", "start_datetime", "end_datetime", "state")
    def _check_no_overlap(self):
        for booking in self:
            if booking.state in ("cancelled",):
                continue
            if booking.start_datetime >= booking.end_datetime:
                raise UserError(_("End time must be after start time."))
            overlapping = self.search([
                ("asset_id", "=", booking.asset_id.id),
                ("state", "in", ("upcoming", "ongoing")),
                ("id", "!=", booking.id),
                ("start_datetime", "<", booking.end_datetime),
                ("end_datetime", ">", booking.start_datetime),
            ])
            if overlapping:
                raise UserError(_(
                    "Resource %s is already booked for the selected time slot.",
                    booking.asset_id.name
                ))

    def action_cancel(self):
        for b in self:
            b.write({"state": "cancelled"})
