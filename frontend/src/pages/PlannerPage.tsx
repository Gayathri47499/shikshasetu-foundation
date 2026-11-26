import React, { useEffect, useState } from "react";
import { Calendar, Check, Download, Sparkles, X } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../lib/api";
import { Card, DisclaimerBanner, LoadingSkeleton, PriorityBadge, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";

function getMondayISO(): string {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().split("T")[0];
}

export const PlannerPage: React.FC = () => {
  const { user } = useAuth();
  const [weekStart, setWeekStart] = useState(getMondayISO());
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [maxPropose, setMaxPropose] = useState(7);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadPlan = () => {
    setLoading(true);
    api
      .get("/api/planner/weekly", { params: { week_start_date: weekStart } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPlan();
  }, [weekStart]);

  const handlePropose = async () => {
    setMessage("");
    setError("");
    try {
      const res = await api.post("/api/planner/propose", {
        week_start_date: weekStart,
        max_visits_to_propose: maxPropose,
      });
      setMessage(res.data.message);
      loadPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Could not generate proposals.");
    }
  };

  const handleApprove = async (id: number, decision: "approved" | "rejected") => {
    setMessage("");
    setError("");
    try {
      const res = await api.post(`/api/planner/${id}/approve`, { decision });
      setMessage(res.data.message);
      loadPlan();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Approval failed.");
    }
  };

  const handleDownloadOfflineTasks = async () => {
    const res = await api.get("/api/planner/offline-tasks/csv", {
      params: { week_start_date: weekStart },
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `shikshasetu_tasks_${weekStart}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (loading && !data) return <LoadingSkeleton rows={5} />;
  if (!data) return null;

  const { constraints, worker_workload, schedules } = data;
  const canApprove = user?.role === "admin" || user?.role === "teacher";

  return (
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Intelligent Intervention Planner</h1>
          <p className="text-sm text-[#687482]">
            Capacity- & budget-constrained outreach allocation (Dataset A3: 5 workers, max 4/day, 100/wk, ₹25,000/wk).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <input
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-xs font-medium bg-white"
          />
          <button
            onClick={handleDownloadOfflineTasks}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-[#F6C9D5] text-xs font-semibold text-[#C05D7E] hover:bg-[#FFF1F5]"
          >
            <Download className="w-4 h-4" /> Offline Task CSV
          </button>
          {canApprove && (
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={1}
                max={25}
                value={maxPropose}
                onChange={(e) => setMaxPropose(Number(e.target.value))}
                className="w-16 px-2.5 py-2 rounded-xl border border-[#F3DCE3] text-xs text-center"
                title="Max visits to propose"
              />
              <button
                onClick={handlePropose}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#D97998] hover:bg-[#C05D7E] text-white text-xs font-semibold"
              >
                <Sparkles className="w-4 h-4" /> Propose Weekly Queue
              </button>
            </div>
          )}
        </div>
      </div>

      <DisclaimerBanner title="Human-Approval Gate & Constraint Enforcement">
        Generated proposals start as <strong>Proposed</strong> and are never auto-assigned. Teacher Coordinator or
        Administrator approval is required before a visit enters the active outreach queue. All daily (4/worker/day),
        weekly (100/week), and budget (₹25,000/week @ ₹250/visit) rules are strictly enforced server-side.
      </DisclaimerBanner>

      {message && (
        <div className="p-3 rounded-xl bg-[#E8F5EC] border border-[#CBE7D4] text-xs text-[#3B7F60] font-medium">
          {message}
        </div>
      )}
      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">{error}</div>
      )}

      {/* Constraint Gauges */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Approved Visits This Week</p>
          <p className="text-2xl font-extrabold text-[#28313B] mt-1">
            {constraints.total_visits} / {constraints.max_weekly_visits}
          </p>
          <p className="text-xs text-[#4D9B78] mt-1">{constraints.remaining_capacity} slots remaining</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Weekly Budget Utilized</p>
          <p className="text-2xl font-extrabold text-[#28313B] mt-1">
            ₹{constraints.total_cost_inr.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-[#687482] mt-1">
            Cap: ₹{constraints.weekly_budget_inr.toLocaleString("en-IN")} (₹250/visit)
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Active Outreach Team</p>
          <p className="text-2xl font-extrabold text-[#28313B] mt-1">5 Workers</p>
          <p className="text-xs text-[#687482] mt-1">Max 4 visits/worker/day × 5 days</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Pending Approval</p>
          <p className="text-2xl font-extrabold text-[#D97998] mt-1">
            {schedules.filter((s: any) => s.approval_status === "proposed").length}
          </p>
          <p className="text-xs text-[#687482] mt-1">Awaiting coordinator sign-off</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-5">
          <h2 className="font-bold text-base mb-1">Worker Weekly Allocation</h2>
          <p className="text-xs text-[#687482] mb-3">Approved vs Proposed (max 20/worker/week)</p>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={worker_workload}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3DCE3" />
                <XAxis dataKey="worker_id" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 20]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="approved_visits" name="Approved" stackId="a" fill="#4D9B78" />
                <Bar dataKey="proposed_visits" name="Proposed" stackId="a" fill="#F6C9D5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="lg:col-span-2 overflow-hidden">
          <div className="p-4 border-b border-[#F3DCE3] flex items-center justify-between">
            <h2 className="font-bold text-base flex items-center gap-2">
              <Calendar className="w-4 h-4 text-[#D97998]" />
              Weekly Visit Schedule ({weekStart})
            </h2>
          </div>
          {schedules.length === 0 ? (
            <div className="p-8 text-center text-sm text-[#687482]">
              No visits scheduled for this week yet. Click <strong>Propose Weekly Queue</strong> to generate a
              capacity-validated plan.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[#FFF1F5] text-xs text-[#687482] uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Student</th>
                    <th className="px-4 py-3 text-left">Worker</th>
                    <th className="px-4 py-3 text-left">Priority</th>
                    <th className="px-4 py-3 text-left">Approval</th>
                    {canApprove && <th className="px-4 py-3 text-right">Action</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F3DCE3]">
                  {schedules.map((s: any) => (
                    <tr key={s.id} className="hover:bg-[#FFF9FB]">
                      <td className="px-4 py-3 text-xs font-medium">{s.visit_date}</td>
                      <td className="px-4 py-3">
                        <p className="font-bold">{s.student_id}</p>
                        <p className="text-[11px] text-[#687482]">School {s.school_id}</p>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {s.worker_name} ({s.worker_id})
                      </td>
                      <td className="px-4 py-3">
                        <PriorityBadge band={s.priority_band_snapshot} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={s.approval_status} />
                      </td>
                      {canApprove && (
                        <td className="px-4 py-3 text-right">
                          {s.approval_status === "proposed" ? (
                            <div className="inline-flex gap-1.5">
                              <button
                                onClick={() => handleApprove(s.id, "approved")}
                                className="p-1.5 rounded-lg bg-[#E8F5EC] text-[#3B7F60] hover:bg-[#CBE7D4]"
                                title="Approve visit"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleApprove(s.id, "rejected")}
                                className="p-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100"
                                title="Reject proposal"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ) : (
                            <span className="text-xs text-[#687482]">—</span>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
