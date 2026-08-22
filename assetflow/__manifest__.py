{
    "name": "AssetFlow",
    "version": "18.0.1.0.0",
    "category": "Operations",
    "summary": "Enterprise Asset & Resource Management System",
    "description": """
AssetFlow
=========
Track, allocate and maintain physical assets and book shared resources.
Includes departments, categories, employee directory, asset lifecycle,
allocations, transfers, bookings, maintenance requests and audit cycles.
""",
    "author": "kaushik jasoliya",
    "license": "LGPL-3",
    "depends": ["base", "mail", "web"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/security_rules.xml",
        "data/ir_sequence_data.xml",
        "data/cron_data.xml",
        "data/mail_template_data.xml",
        "data/assetflow_demo_data.xml",
        "views/department_views.xml",
        "views/category_views.xml",
        "views/employee_views.xml",
        "views/asset_views.xml",
        "views/allocation_views.xml",
        "views/transfer_views.xml",
        "views/booking_views.xml",
        "views/maintenance_request_views.xml",
        "views/audit_views.xml",
        "views/dashboard_views.xml",
        "views/dashboard_templates.xml",
        "views/menus.xml",
        "report/asset_report.xml",
    ],
    "demo": [
        "demo/demo_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "assetflow/static/src/js/**/*.js",
            "assetflow/static/src/xml/**/*.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}