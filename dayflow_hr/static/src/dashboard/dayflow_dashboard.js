/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { EmployeeDashboard } from "@dayflow_hr/dashboard/employee_dashboard";
import { AdminDashboard } from "@dayflow_hr/dashboard/admin_dashboard";

export class DayflowDashboard extends Component {
    static template = "dayflow_hr.DayflowDashboard";
    static components = { EmployeeDashboard, AdminDashboard };
    static props = ["*"];

    setup() {
        this.state = useState({ loading: true, isAdmin: false });
        onWillStart(async () => {
            this.state.isAdmin = await user.hasGroup("hr.group_hr_user");
            this.state.loading = false;
        });
    }
}

registry.category("actions").add("dayflow_dashboard_action", DayflowDashboard);
