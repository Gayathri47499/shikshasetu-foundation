import React, { useEffect, useState } from "react";
import { AlertCircle, Award, School as SchoolIcon, Users } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../lib/api";
import { Card, LoadingSkeleton, PriorityBadge } from "../components/ui";

export const SchoolsPage: React.FC = () => {
  const [schoolsData, setSchoolsData] = useState<any>(null);
  const [selectedSchoolId, setSelectedSchoolId] = useState<number | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/schools")
      .then((res) => {
        setSchoolsData(res.data);
        if (res.data.schools.length > 0) {
          setSelectedSchoolId(res.data.schools[0].id);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedSchoolId !== null) {
      api.get(`/api/schools/${selectedSchoolId}`).then((res) => setDetail(res.data));
    }
  }, [selectedSchoolId]);

  if (loading) return <LoadingSkeleton rows={5} />;
  if (!schoolsData) return null;

  const { schools, summary } = schoolsData;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#28313B]">School Analytics & Cluster Comparison</h1>
        <p className="text-sm text-[#687482]">
          Baseline enrollment and attendance rankings across ShikshaSetu Foundation schools (Dataset A1).
        </p>
      </div>

      {/* Top Summary Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Schools Active</p>
          <p className="text-2xl font-extrabold text-[#28313B] mt-1">{summary.total_schools}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Total Enrolled</p>
          <p className="text-2xl font-extrabold text-[#28313B] mt-1">{summary.total_enrolled_students}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Weighted Avg Attendance</p>
          <p className="text-2xl font-extrabold text-[#4D9B78] mt-1">{summary.weighted_average_attendance_pct}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Schools Below 70%</p>
          <p className="text-2xl font-extrabold text-[#D97998] mt-1">{summary.schools_below_70_pct}</p>
        </Card>
      </div>

      {/* Comparative Bar Chart */}
      <Card className="p-5">
        <h2 className="font-bold text-base text-[#28313B] mb-1">Attendance Ranking (Lowest to Highest)</h2>
        <p className="text-xs text-[#687482] mb-4">Click any school row below to inspect its detailed profile.</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={schools}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3DCE3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="baseline_attendance_pct" name="Avg Attendance %" radius={[8, 8, 0, 0]}>
                {schools.map((s: any) => (
                  <Cell key={s.id} fill={s.requires_attention ? "#D97998" : "#4D9B78"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* School Table */}
        <Card className="lg:col-span-2 overflow-hidden">
          <div className="p-4 border-b border-[#F3DCE3]">
            <h2 className="font-bold text-base">All Schools Directory</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#FFF1F5] text-xs text-[#687482] uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Rank</th>
                  <th className="px-4 py-3 text-left">School</th>
                  <th className="px-4 py-3 text-left">Coordinator</th>
                  <th className="px-4 py-3 text-right">Enrolled</th>
                  <th className="px-4 py-3 text-right">Avg Attendance</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3DCE3]">
                {schools.map((sc: any) => (
                  <tr
                    key={sc.id}
                    onClick={() => setSelectedSchoolId(sc.id)}
                    className={`cursor-pointer transition-colors ${
                      selectedSchoolId === sc.id ? "bg-[#FFF1F5]" : "hover:bg-[#FFF9FB]"
                    }`}
                  >
                    <td className="px-4 py-3 font-semibold text-[#687482]">#{sc.attendance_rank}</td>
                    <td className="px-4 py-3 font-semibold text-[#28313B]">
                      {sc.name} <span className="text-xs text-[#687482]">({sc.code})</span>
                    </td>
                    <td className="px-4 py-3 text-[#687482]">{sc.coordinator_name}</td>
                    <td className="px-4 py-3 text-right font-medium">{sc.enrolled_students}</td>
                    <td className="px-4 py-3 text-right font-bold">{sc.baseline_attendance_pct}%</td>
                    <td className="px-4 py-3">
                      {sc.requires_attention ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                          <AlertCircle className="w-3 h-3" /> Attention
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#3B7F60] bg-[#E8F5EC] px-2.5 py-0.5 rounded-full border border-[#CBE7D4]">
                          <Award className="w-3 h-3" /> Stable
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Detailed Selected School Profile */}
        <Card className="p-5">
          {detail ? (
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-semibold text-[#D97998]">{detail.school.code}</span>
                  <h3 className="text-xl font-bold text-[#28313B]">{detail.school.name}</h3>
                  <p className="text-xs text-[#687482]">Coordinator: {detail.school.coordinator_name}</p>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FFF1F5] text-[#D97998]">
                  <SchoolIcon className="w-5 h-5" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 rounded-xl bg-[#FFF9FB] border border-[#F3DCE3]">
                  <p className="text-xs text-[#687482]">Enrolled</p>
                  <p className="text-lg font-bold text-[#28313B]">{detail.school.enrolled_students}</p>
                </div>
                <div className="p-3 rounded-xl bg-[#FFF9FB] border border-[#F3DCE3]">
                  <p className="text-xs text-[#687482]">Baseline Att.</p>
                  <p className="text-lg font-bold text-[#D97998]">{detail.school.baseline_attendance_pct}%</p>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-[#28313B] mb-2">Sample Weekly Trend</p>
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={detail.weekly_trend}>
                      <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                      <YAxis domain={[20, 100]} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="avg_attendance_pct" stroke="#D97998" strokeWidth={2.5} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-[#28313B] mb-2 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-[#D97998]" />
                  Tracked Student Sample ({detail.students.length})
                </p>
                <div className="space-y-2">
                  {detail.students.map((st: any) => (
                    <div key={st.id} className="p-2.5 rounded-xl border border-[#F3DCE3] flex items-center justify-between text-xs">
                      <div>
                        <p className="font-bold text-[#28313B]">{st.id}</p>
                        <p className="text-[#687482]">
                          Att: {st.attendance_pct}% • Score: {st.previous_term_score} • {st.distance_km} km
                        </p>
                      </div>
                      <PriorityBadge band={st.effective_band} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <LoadingSkeleton rows={3} />
          )}
        </Card>
      </div>
    </div>
  );
};
