import re

from odoo import http, _
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


class DayflowVerificationPending(Exception):
    """Raised when signup succeeded but the account is inactive pending email verification."""


class DayflowAuthSignupHome(AuthSignupHome):

    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext)
        employee_code = (request.params.get("dayflow_employee_code") or "").strip()
        requested_role = request.params.get("dayflow_requested_role") or "employee"
        if requested_role not in ("employee", "hr"):
            requested_role = "employee"
        if not employee_code:
            raise UserError(_("Employee ID is required to sign up."))
        password = values.get("password") or ""
        if not PASSWORD_RE.match(password):
            raise UserError(_("Password must be at least 8 characters long and include both letters and numbers."))
        values["dayflow_employee_code"] = employee_code
        values["dayflow_requested_role"] = requested_role
        return values

    def _signup_with_values(self, token, values):
        try:
            return super()._signup_with_values(token, values)
        except AccessDenied:
            raise DayflowVerificationPending(values.get("login"))

    @http.route("/web/signup", type="http", auth="public", website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        try:
            return super().web_auth_signup(*args, **kw)
        except DayflowVerificationPending:
            qcontext = self.get_auth_signup_qcontext()
            qcontext["message"] = _(
                "Account created! We've sent a verification link to your email address. "
                "Please verify it before signing in."
            )
            response = request.render("auth_signup.signup", qcontext)
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
            return response

    @http.route("/dayflow/verify/<string:token>", type="http", auth="public", website=True, sitemap=False)
    def dayflow_verify_email(self, token, **kw):
        verified = request.env["res.users"].sudo().action_dayflow_verify_email(token)
        return request.render("dayflow_hr.email_verification_result", {"success": verified})
