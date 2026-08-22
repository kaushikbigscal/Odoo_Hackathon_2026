/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

const LEAVE_STATE_LABELS = {
    draft: "Draft",
    confirm: "Pending",
    validate1: "Pending (2nd approval)",
    validate: "Approved",
    refuse: "Rejected",
    cancel: "Cancelled",
};

export class EmployeeDashboard extends Component {
    static template = "dayflow_hr.EmployeeDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ recentLeaves: [], loading: true });
        onWillStart(async () => {
            this.state.recentLeaves = await this.orm.searchRead(
                "hr.leave",
                [["employee_id.user_id", "=", user.userId]],
                ["holiday_status_id", "date_from", "date_to", "state"],
                { order: "create_date desc", limit: 5 }
            );
            this.state.loading = false;
        });
    }

    leaveStateLabel(state) {
        return LEAVE_STATE_LABELS[state] || state;
    }

    openProfile() {
        this.action.doAction("dayflow_hr.action_dayflow_my_profile");
    }

    openAttendance() {
        this.action.doAction("dayflow_hr.action_dayflow_attendance_day_my");
    }

    openLeaves() {
        this.action.doAction("hr_holidays.hr_leave_action_my");
    }

    logout() {
        window.location.href = "/web/session/logout";
    }
}
