{
    "name": "Dayflow HR",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Dayflow — Human Resource Management System",
    "description": """
Dayflow HR
==========
Every workday, perfectly aligned.

Adds a self-service sign-up flow, role-based dashboards, attendance and
leave reporting, a lightweight payroll module and analytics on top of
Odoo's stock HR apps.
""",
    "author": "kaushik jasoliya",
    "license": "LGPL-3",
    "depends": ["base", "mail", "web", "hr", "hr_attendance", "hr_holidays", "hr_contract", "auth_signup"],
    "data": [
        "security/ir.model.access.csv",
        "security/dayflow_security.xml",
        "data/dayflow_salary_rule_data.xml",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "views/auth_signup_templates.xml",
        "views/dayflow_actions.xml",
        "views/dayflow_attendance_day_views.xml",
        "views/dayflow_payslip_views.xml",
        "views/dayflow_analytics_views.xml",
        "report/dayflow_payslip_report.xml",
        "views/dayflow_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dayflow_hr/static/src/dashboard/*.scss",
            "dayflow_hr/static/src/dashboard/*.js",
            "dayflow_hr/static/src/dashboard/*.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "_dayflow_hr_post_init",
}
