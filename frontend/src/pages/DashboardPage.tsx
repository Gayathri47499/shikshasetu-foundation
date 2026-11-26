import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  ArrowUpRight,
  CalendarCheck,
  CheckCircle2,
  IndianRupee,
  School as SchoolIcon,
  Users,
} from "lucide-react";
import api from "../lib/api";
import { AnimatedCounter, Card, DisclaimerBanner, LoadingSkeleton } from "../components/ui";
import { TeacherHelpingIllustration } from "../components/Illustrations";

const PRIORITY_COLORS = ["#D97998", "#F4A261", "#4D9B78"];

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [schoolFilter, setSchoolFilter] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const fetchDashboard = () => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (schoolFilter) params.school_id = schoolFilter;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    api
      .get("/api/dashboard", { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboard();
  }, [schoolFilter, dateFrom, dateTo]);

  if (loading && !data) return <LoadingSkeleton rows={6} />;
  if (!data) return null;

  const { kpis, charts, recent_activities, data_freshness } = data;

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Foundation Intelligence Dashboard</h1>
          <p className="text-sm text-[#687482] mt-0.5">
            Live overview across ShikshaSetu Foundation schools, review priorities, and outreach budget.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={schoolFilter}
            onChange={(e) => setSchoolFilter(e.target.value)}
            aria-label="Filter by school"
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] bg-white text-xs font-medium text-[#28313B]"
          >
            <option value="">All Authorized Schools</option>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <option key={num} value={num}>
                School {num}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            aria-label="Date from"
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] bg-white text-xs text-[#28313B]"
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            aria-label="Date to"
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] bg-white text-xs text-[#28313B]"
          />
          {(schoolFilter || dateFrom || dateTo) && (
            <button
              onClick={() => {
                setSchoolFilter("");
                setDateFrom("");
                setDateTo("");
              }}
              className="px-3 py-2 rounded-xl bg-[#FFF1F5] text-[#C05D7E] text-xs font-semibold border border-[#F6C9D5]"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      <DisclaimerBanner title={data_freshness.assessment_baseline}>
        {data_freshness.synthetic_disclaimer}
      </DisclaimerBanner>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card hover className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#687482]">Total Enrolled Students</span>
            <div className="p-2 rounded-xl bg-[#FFF1F5] text-[#D97998]">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-[#28313B] mt-2">
            <AnimatedCounter value={kpis.total_students_enrolled} />
          </p>
          <p className="text-xs text-[#687482] mt-1">
            Across {kpis.total_schools} schools • {kpis.tracked_student_profiles} illustrative profiles
          </p>
        </Card>

        <Card hover className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#687482]">Weighted Avg Attendance</span>
            <div className="p-2 rounded-xl bg-[#E8F5EC] text-[#4D9B78]">
              <SchoolIcon className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-[#28313B] mt-2">
            <AnimatedCounter value={kpis.average_attendance_pct} decimals={1} suffix="%" />
          </p>
          <p className="text-xs text-[#687482] mt-1">Lowest: School 7 (61%) • Highest: School 1 (82%)</p>
        </Card>

        <Card hover className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#687482]">Requiring Review / High Priority</span>
            <div className="p-2 rounded-xl bg-rose-50 text-rose-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-[#28313B] mt-2">
            <AnimatedCounter value={kpis.students_requiring_review} />
            <span className="text-base font-semibold text-rose-600 ml-2">
              ({kpis.high_priority_cases} high)
            </span>
          </p>
          <p className="text-xs text-[#687482] mt-1">Operational triage queue (human validation required)</p>
        </Card>

        <Card hover className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#687482]">Weekly Capacity & Budget</span>
            <div className="p-2 rounded-xl bg-[#FFF1F5] text-[#D97998]">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-[#28313B] mt-2">
            {kpis.weekly_intervention_visits}/{kpis.max_weekly_visits}
            <span className="text-xs font-medium text-[#687482] ml-2">visits</span>
          </p>
          <p className="text-xs text-[#687482] mt-1">
            ₹{kpis.weekly_budget_used_inr.toLocaleString("en-IN")} / ₹{kpis.weekly_budget_limit_inr.toLocaleString("en-IN")} ({kpis.budget_utilization_pct}%)
          </p>
        </Card>
      </div>

      {/* Secondary Operational Strip + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-[#687482]">Completed Interventions</p>
            <p className="text-2xl font-bold text-[#4D9B78] mt-1">{kpis.completed_interventions}</p>
            <p className="text-xs text-[#687482] mt-0.5">{kpis.pending_followups} pending follow-up/outcome</p>
          </div>
          <CheckCircle2 className="w-9 h-9 text-[#4D9B78]/70" />
        </Card>

        <Card className="p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-[#687482]">Remaining Weekly Visit Capacity</p>
            <p className="text-2xl font-bold text-[#28313B] mt-1">{kpis.remaining_visit_capacity} visits</p>
            <p className="text-xs text-[#687482] mt-0.5">5 workers × 4 visits/day × 5 days</p>
          </div>
          <CalendarCheck className="w-9 h-9 text-[#D97998]/80" />
        </Card>

        <Card className="p-4 bg-[#FFF1F5]/70 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-[#28313B]">Quick Actions</p>
            <div className="flex flex-wrap gap-2 mt-2">
              <button
                onClick={() => navigate("/risk-intelligence")}
                className="px-3 py-1.5 rounded-lg bg-[#D97998] text-white text-xs font-semibold inline-flex items-center gap-1"
              >
                Review Queue <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => navigate("/planner")}
                className="px-3 py-1.5 rounded-lg bg-white border border-[#F6C9D5] text-[#28313B] text-xs font-semibold"
              >
                Weekly Planner
              </button>
              <button
                onClick={() => navigate("/assistant")}
                className="px-3 py-1.5 rounded-lg bg-white border border-[#F6C9D5] text-[#C05D7E] text-xs font-semibold"
              >
                Ask AI
              </button>
            </div>
          </div>
          <TeacherHelpingIllustration className="w-24 h-20 shrink-0 hidden sm:block" />
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-base text-[#28313B]">School-wise Attendance Comparison</h2>
              <p className="text-xs text-[#687482]">Exact Dataset A1 baseline (%) — Rose highlights schools &lt; 70%</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.school_attendance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3DCE3" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#687482" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#687482" }} unit="%" />
                <Tooltip />
                <Bar dataKey="attendance_pct" name="Avg Attendance %" radius={[8, 8, 0, 0]}>
                  {charts.school_attendance.map((entry: any) => (
                    <Cell
                      key={entry.school_id}
                      fill={entry.requires_attention ? "#D97998" : "#4D9B78"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <div className="mb-4">
            <h2 className="font-bold text-base text-[#28313B]">Weekly Attendance Trend</h2>
            <p className="text-xs text-[#687482]">Mean student sample attendance across recorded weeks (illustrative + A2)</p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts.weekly_trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3DCE3" />
                <XAxis dataKey="week" tick={{ fontSize: 11, fill: "#687482" }} />
                <YAxis domain={[40, 100]} tick={{ fontSize: 11, fill: "#687482" }} unit="%" />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="avg_attendance_pct"
                  name="Mean Attendance %"
                  stroke="#D97998"
                  strokeWidth={3}
                  dot={{ r: 5, fill: "#D97998" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Charts Row 2 + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-5">
          <h2 className="font-bold text-base text-[#28313B]">Priority Band Distribution</h2>
          <p className="text-xs text-[#687482] mb-2">Operational review triage bands</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.priority_distribution}
                  dataKey="count"
                  nameKey="band"
                  innerRadius={45}
                  outerRadius={78}
                  paddingAngle={4}
                >
                  {charts.priority_distribution.map((_: any, idx: number) => (
                    <Cell key={idx} fill={PRIORITY_COLORS[idx % PRIORITY_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs">
            {charts.priority_distribution.map((d: any, idx: number) => (
              <span key={d.band} className="flex items-center gap-1.5">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: PRIORITY_COLORS[idx % PRIORITY_COLORS.length] }}
                />
                {d.band}: <strong>{d.count}</strong>
              </span>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="font-bold text-base text-[#28313B]">Outreach Team Workload</h2>
          <p className="text-xs text-[#687482] mb-3">5 Workers • Max 20 visits/worker/week</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.outreach_performance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#F3DCE3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="worker_id" type="category" tick={{ fontSize: 11 }} width={46} />
                <Tooltip />
                <Bar dataKey="completed" name="Completed" stackId="a" fill="#4D9B78" />
                <Bar dataKey="pending" name="Pending" stackId="a" fill="#F6C9D5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="font-bold text-base text-[#28313B]">Recent Audit Activities</h2>
          <p className="text-xs text-[#687482] mb-3">Server-logged governance events</p>
          <div className="space-y-2.5 max-h-60 overflow-y-auto custom-scrollbar pr-1">
            {recent_activities.map((act: any) => (
              <div key={act.id} className="p-2.5 rounded-xl bg-[#FFF9FB] border border-[#F3DCE3] text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#28313B]">{act.action.replace(/_/g, " ")}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF1F5] text-[#C05D7E]">
                    {act.actor_role}
                  </span>
                </div>
                <p className="text-[#687482] mt-0.5 truncate">
                  {act.record_type}: {act.record_id}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
