from odoo import models, fields, api


class AssetFlowDashboard(models.TransientModel):
    _name = "assetflow.dashboard"
    _description = "AssetFlow Dashboard"

    name = fields.Char(default="AssetFlow Dashboard")
    html = fields.Html(compute="_compute_html", sanitize=False)

    def _compute_html(self):
        for rec in self:
            rec.html = self.env['ir.qweb']._render('assetflow.dashboard_content', self._values())

    def _values(self):
        env = self.env
        Asset = env['assetflow.asset']
        total_assets = Asset.search_count([])
        states = {
            'available': Asset.search_count([('state', '=', 'available')]),
            'allocated': Asset.search_count([('state', '=', 'allocated')]),
            'reserved': Asset.search_count([('state', '=', 'reserved')]),
            'under_maintenance': Asset.search_count([('state', '=', 'under_maintenance')]),
            'lost': Asset.search_count([('state', '=', 'lost')]),
            'retired': Asset.search_count([('state', '=', 'retired')]),
        }
        pending_transfers = env['assetflow.transfer'].search_count([('state', '=', 'requested')])
        active_bookings = env['assetflow.booking'].search_count([('state', '=', 'ongoing')])
        upcoming_bookings = env['assetflow.booking'].search_count([('state', '=', 'upcoming')])
        open_maint = env['assetflow.maintenance.request'].search_count(
            [('state', 'in', ('pending', 'approved', 'technician_assigned', 'in_progress'))])
        dist = [
            {'label': 'Available', 'count': states['available'], 'color': '#1e9e6a'},
            {'label': 'Allocated', 'count': states['allocated'], 'color': '#2f80ed'},
            {'label': 'Reserved', 'count': states['reserved'], 'color': '#9b51e0'},
            {'label': 'Under Maintenance', 'count': states['under_maintenance'], 'color': '#f2994a'},
            {'label': 'Lost', 'count': states['lost'], 'color': '#eb5757'},
            {'label': 'Retired', 'count': states['retired'], 'color': '#828282'},
        ]
        max_dist = max((d['count'] for d in dist), default=1) or 1
        for d in dist:
            d['style'] = "width:%d%%; background:%s;" % (
                round(d['count'] / max_dist * 100) if max_dist else 0, d['color'])

        def act(xmlid):
            return '/web#action=%s' % env.ref(xmlid).id

        return {
            'kpis': [
                ('Total Assets', total_assets, '#0b2545'),
                ('Available', states['available'], '#1e9e6a'),
                ('Allocated', states['allocated'], '#2f80ed'),
                ('Pending Transfers', pending_transfers, '#f2c94c'),
                ('Active Bookings', active_bookings, '#9b51e0'),
                ('Open Maintenance', open_maint, '#f2994a'),
            ],
            'dept_count': env['assetflow.department'].search_count([]),
            'cat_count': env['assetflow.category'].search_count([]),
            'emp_count': env['assetflow.employee'].search_count([]),
            'upcoming_bookings': upcoming_bookings,
            'dist': dist, 'max_dist': max_dist,
            'recent_assets': Asset.search([], order='create_date desc', limit=6),
            'recent_bookings': env['assetflow.booking'].search([], order='create_date desc', limit=5),
            'recent_alloc': env['assetflow.allocation'].search([], order='create_date desc', limit=5),
            'links': {
                'asset': act('assetflow.action_assetflow_asset'),
                'employee': act('assetflow.action_assetflow_employee'),
                'allocation': act('assetflow.action_assetflow_allocation'),
                'transfer': act('assetflow.action_assetflow_transfer'),
                'booking': act('assetflow.action_assetflow_booking'),
                'maintenance': act('assetflow.action_assetflow_maintenance_request'),
                'audit': act('assetflow.action_assetflow_audit_cycle'),
                'department': act('assetflow.action_assetflow_department'),
                'category': act('assetflow.action_assetflow_category'),
            },
        }
