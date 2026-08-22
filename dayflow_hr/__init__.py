from datetime import timedelta

from odoo import fields

from . import models
from . import controllers


def _dayflow_hr_post_init(env):
    # Enable public ("Free sign up") self-registration so employees can
    # create their own account from the Employee ID they were given.
    env["ir.config_parameter"].sudo().set_param("auth_signup.invitation_scope", "b2c")
    # When the `website` module is installed, res.users._get_signup_invitation_scope()
    # prefers each website's own "Customer Account" setting over the global
    # config parameter above, so it must be switched to "Free sign up" too.
    if "website" in env.registry:
        env["website"].sudo().search([]).write({"auth_signup_uninvited": "b2c"})

    # Backfill attendance status history so the report isn't empty right
    # after install.
    today = fields.Date.context_today(env["dayflow.attendance.day"])
    employees = env["hr.employee"].search([])
    env["dayflow.attendance.day"]._dayflow_recompute(employees, today - timedelta(days=30), today)
