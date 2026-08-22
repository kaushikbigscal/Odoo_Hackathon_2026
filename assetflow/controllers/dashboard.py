from odoo import http
from odoo.http import request


class AssetFlowDashboard(http.Controller):

    @http.route('/asset/dashboard', type='http', auth='user', website=False)
    def dashboard(self, **kw):
        env = request.env
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
        dept_count = env['assetflow.department'].search_count([])
        cat_count = env['assetflow.category'].search_count([])
        emp_count = env['assetflow.employee'].search_count([])
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

        recent_assets = Asset.search([], order='create_date desc', limit=6)
        recent_bookings = env['assetflow.booking'].search([], order='create_date desc', limit=5)
        recent_alloc = env['assetflow.allocation'].search([], order='create_date desc', limit=5)

        def act(xmlid):
            return '/web#action=%s' % env.ref(xmlid).id

        values = {
            'kpis': [
                ('Total Assets', total_assets, '#0b2545'),
                ('Available', states['available'], '#1e9e6a'),
                ('Allocated', states['allocated'], '#2f80ed'),
                ('Pending Transfers', pending_transfers, '#f2c94c'),
                ('Active Bookings', active_bookings, '#9b51e0'),
                ('Open Maintenance', open_maint, '#f2994a'),
            ],
            'dept_count': dept_count, 'cat_count': cat_count, 'emp_count': emp_count,
            'upcoming_bookings': upcoming_bookings,
            'dist': dist, 'max_dist': max_dist,
            'recent_assets': recent_assets,
            'recent_bookings': recent_bookings,
            'recent_alloc': recent_alloc,
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
        return request.render('assetflow.dashboard_template', values)
