/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AdminDashboard extends Component {
    static template = "dayflow_hr.AdminDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            kpis: { employees: 0, presentToday: 0, pendingLeaves: 0, pendingRoles: 0, payrollCost: 0 },
            employees: [],
            selectedEmployee: null,
            selectedDetail: null,
            pendingLeaves: [],
            pendingRoles: [],
        });
        onWillStart(() => this.loadAll());
    }

    async loadAll() {
        await Promise.all([
            this.loadKpis(),
            this.loadEmployees(),
            this.loadPendingLeaves(),
            this.loadPendingRoles(),
        ]);
        this.state.loading = false;
    }

    async loadKpis() {
        const now = new Date();
        const pad = (n) => String(n).padStart(2, "0");
        const monthStart = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`;
        const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        const monthEnd = `${nextMonth.getFullYear()}-${pad(nextMonth.getMonth() + 1)}-01`;

        const [employees, presentToday, pendingLeaves, pendingRoles, payrollGroups] = await Promise.all([
            this.orm.searchCount("hr.employee", [["active", "=", true]]),
            this.orm.searchCount("hr.attendance", [["check_out", "=", false]]),
            this.orm.searchCount("hr.leave", [["state", "in", ["confirm", "validate1"]]]),
            this.orm.searchCount("res.users", [["dayflow_role_status", "=", "pending"]]),
            this.orm.readGroup(
                "dayflow.payslip",
                [["state", "in", ["confirmed", "paid"]], ["date_from", ">=", monthStart], ["date_from", "<", monthEnd]],
                ["net_pay:sum"],
                []
            ),
        ]);
        const payrollCost = payrollGroups.length ? payrollGroups[0].net_pay : 0;
        Object.assign(this.state.kpis, { employees, presentToday, pendingLeaves, pendingRoles, payrollCost });
    }

    async loadEmployees() {
        this.state.employees = await this.orm.searchRead(
            "hr.employee",
            [["active", "=", true]],
            ["name", "job_title", "department_id", "work_email"],
            { limit: 200, order: "name" }
        );
    }

    async loadPendingLeaves() {
        const leaves = await this.orm.searchRead(
            "hr.leave",
            [["state", "in", ["confirm", "validate1"]]],
            ["employee_id", "holiday_status_id", "date_from", "date_to", "state"],
            { limit: 20, order: "create_date desc" }
        );
        this.state.pendingLeaves = leaves.map((leave) => ({ ...leave, comment: "" }));
    }

    async loadPendingRoles() {
        this.state.pendingRoles = await this.orm.searchRead(
            "res.users",
            [["dayflow_role_status", "=", "pending"]],
            ["name", "login", "dayflow_employee_code"],
            { limit: 20 }
        );
    }

    async selectEmployee(employee) {
        this.state.selectedEmployee = employee;
        const [checkedInCount, pendingLeaveCount] = await Promise.all([
            this.orm.searchCount("hr.attendance", [
                ["employee_id", "=", employee.id],
                ["check_out", "=", false],
            ]),
            this.orm.searchCount("hr.leave", [
                ["employee_id", "=", employee.id],
                ["state", "in", ["confirm", "validate1"]],
            ]),
        ]);
        this.state.selectedDetail = {
            checkedIn: checkedInCount > 0,
            pendingLeaves: pendingLeaveCount,
        };
    }

    async _postLeaveComment(leave) {
        const comment = (leave.comment || "").trim();
        if (!comment) {
            return;
        }
        await this.orm.call("hr.leave", "message_post", [[leave.id]], {
            body: comment,
            message_type: "comment",
            subtype_xmlid: "mail.mt_comment",
        });
    }

    async approveLeave(leave) {
        try {
            await this._postLeaveComment(leave);
            await this.orm.call("hr.leave", "action_approve", [[leave.id]]);
            this.notification.add("Leave approved.", { type: "success" });
        } catch {
            this.notification.add("Could not approve this leave request.", { type: "danger" });
        }
        await Promise.all([this.loadPendingLeaves(), this.loadKpis()]);
    }

    async refuseLeave(leave) {
        try {
            await this._postLeaveComment(leave);
            await this.orm.call("hr.leave", "action_refuse", [[leave.id]]);
            this.notification.add("Leave refused.", { type: "warning" });
        } catch {
            this.notification.add("Could not refuse this leave request.", { type: "danger" });
        }
        await Promise.all([this.loadPendingLeaves(), this.loadKpis()]);
    }

    async approveRole(dayflowUser) {
        try {
            await this.orm.call("res.users", "action_dayflow_approve_role_request", [[dayflowUser.id]]);
            this.notification.add("Role request approved.", { type: "success" });
        } catch {
            this.notification.add("Could not approve this role request.", { type: "danger" });
        }
        await Promise.all([this.loadPendingRoles(), this.loadKpis()]);
    }

    async rejectRole(dayflowUser) {
        try {
            await this.orm.call("res.users", "action_dayflow_reject_role_request", [[dayflowUser.id]]);
            this.notification.add("Role request rejected.", { type: "warning" });
        } catch {
            this.notification.add("Could not reject this role request.", { type: "danger" });
        }
        await Promise.all([this.loadPendingRoles(), this.loadKpis()]);
    }

    openEmployees() {
        this.action.doAction("hr.open_view_employee_list");
    }

    openAttendanceManagement() {
        this.action.doAction("hr_attendance.hr_attendance_management_action");
    }

    openLeaveApprovals() {
        this.action.doAction("hr_holidays.hr_leave_action_action_approve_department");
    }

    openPayrollAnalysis() {
        this.action.doAction("dayflow_hr.action_dayflow_payslip_analysis");
    }

    openAttendanceAnalysis() {
        this.action.doAction("dayflow_hr.action_dayflow_attendance_day_analysis");
    }

    openLeaveAnalysis() {
        this.action.doAction("hr_holidays.action_hr_available_holidays_report");
    }
}
