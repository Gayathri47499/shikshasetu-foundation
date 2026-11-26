import React, { useEffect, useState } from "react";
import { Download, Eye, Search, X } from "lucide-react";
import api, { API_BASE_URL } from "../lib/api";
import { Card, LoadingSkeleton, PriorityBadge, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export const StudentsPage: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [schoolId, setSchoolId] = useState("");
  const [band, setBand] = useState("");
  const [maxAtt, setMaxAtt] = useState("");
  const [page, setPage] = useState(1);

  const [selectedProfile, setSelectedProfile] = useState<any>(null);
  const [obsInput, setObsInput] = useState("");
  const [savingObs, setSavingObs] = useState(false);

  const fetchStudents = () => {
    setLoading(true);
    const params: Record<string, string | number> = { page, page_size: 10 };
    if (search) params.search = search;
    if (schoolId) params.school_id = schoolId;
    if (band) params.priority_band = band;
    if (maxAtt) params.max_attendance = maxAtt;

    api
      .get("/api/students", { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStudents();
  }, [page, schoolId, band, maxAtt]);

  const openProfile = async (studentId: string) => {
    const res = await api.get(`/api/students/${studentId}`);
    setSelectedProfile(res.data);
    setObsInput(res.data.student.teacher_observations || "");
  };

  const saveObservations = async () => {
    if (!selectedProfile) return;
    setSavingObs(true);
    try {
      await api.patch(`/api/students/${selectedProfile.student.id}/observations`, {
        teacher_observations: obsInput,
      });
      await openProfile(selectedProfile.student.id);
    } finally {
      setSavingObs(false);
    }
  };

  const handleExportCsv = async () => {
    const res = await api.get("/api/students/export/csv", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "shikshasetu_students.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Student Profiles & Directory</h1>
          <p className="text-sm text-[#687482]">
            Searchable records (Dataset A2 synthetic records + uploaded rows) with attendance, scores, and interventions.
          </p>
        </div>
        <button
          onClick={handleExportCsv}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-[#F6C9D5] text-sm font-semibold text-[#C05D7E] hover:bg-[#FFF1F5]"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative lg:col-span-2">
            <Search className="w-4 h-4 text-[#687482] absolute left-3.5 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchStudents()}
              placeholder="Search Student ID (e.g. ST009)..."
              className="w-full pl-10 pr-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
            />
          </div>
          <select
            value={schoolId}
            onChange={(e) => {
              setSchoolId(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm bg-white"
          >
            <option value="">All Schools</option>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
              <option key={n} value={n}>
                School {n}
              </option>
            ))}
          </select>
          <select
            value={band}
            onChange={(e) => {
              setBand(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm bg-white"
          >
            <option value="">All Priority Bands</option>
            <option value="High Priority">High Priority</option>
            <option value="Review Soon">Review Soon</option>
            <option value="Routine Review">Routine Review</option>
          </select>
          <select
            value={maxAtt}
            onChange={(e) => {
              setMaxAtt(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm bg-white"
          >
            <option value="">Any Attendance</option>
            <option value="50">Below 50% (Prolonged)</option>
            <option value="65">Below 65%</option>
            <option value="75">Below 75%</option>
          </select>
        </div>
      </Card>

      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#FFF1F5] text-xs text-[#687482] uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Student ID</th>
                  <th className="px-4 py-3 text-left">School</th>
                  <th className="px-4 py-3 text-right">Attendance</th>
                  <th className="px-4 py-3 text-right">Prev. Score</th>
                  <th className="px-4 py-3 text-right">Distance</th>
                  <th className="px-4 py-3 text-center">Prior Visits</th>
                  <th className="px-4 py-3 text-left">Priority Band</th>
                  <th className="px-4 py-3 text-left">Data Tag</th>
                  <th className="px-4 py-3 text-right">Profile</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3DCE3]">
                {data?.items.map((st: any) => (
                  <tr key={st.id} className="hover:bg-[#FFF9FB]">
                    <td className="px-4 py-3 font-bold text-[#28313B]">{st.id}</td>
                    <td className="px-4 py-3 text-[#687482]">{st.school_name}</td>
                    <td className="px-4 py-3 text-right font-semibold">{st.attendance_pct}%</td>
                    <td className="px-4 py-3 text-right">{st.previous_term_score ?? "—"}</td>
                    <td className="px-4 py-3 text-right">{st.distance_km} km</td>
                    <td className="px-4 py-3 text-center">{st.prior_intervention_count}</td>
                    <td className="px-4 py-3">
                      <PriorityBadge band={st.priority_band} />
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#FFF1F5] text-[#687482]">
                        {st.is_synthetic_assessment ? "Synthetic A2" : st.data_source}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openProfile(st.id)}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-[#FFF1F5] text-[#C05D7E] text-xs font-semibold hover:bg-[#F6C9D5]/40"
                      >
                        <Eye className="w-3.5 h-3.5" /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 border-t border-[#F3DCE3] flex items-center justify-between text-xs text-[#687482]">
            <span>
              Showing {data?.items.length || 0} of {data?.total || 0} records
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1.5 rounded-lg border border-[#F3DCE3] disabled:opacity-40"
              >
                Previous
              </button>
              <span>
                Page {page} of {data?.total_pages || 1}
              </span>
              <button
                disabled={page >= (data?.total_pages || 1)}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 rounded-lg border border-[#F3DCE3] disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </Card>
      )}

      {/* Profile Drawer Modal */}
      {selectedProfile && (
        <div className="fixed inset-0 z-50 bg-black/30 flex justify-end">
          <div className="bg-white w-full max-w-xl h-full overflow-y-auto p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#F3DCE3] pb-4">
              <div>
                <span className="text-xs font-semibold text-[#D97998]">
                  {selectedProfile.student.school_name} • {selectedProfile.student.grade_level}
                </span>
                <h2 className="text-xl font-bold text-[#28313B]">Student Profile: {selectedProfile.student.id}</h2>
              </div>
              <button
                onClick={() => setSelectedProfile(null)}
                className="p-2 rounded-xl hover:bg-[#FFF1F5]"
                aria-label="Close profile"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-xl bg-[#FFF1F5]">
                <p className="text-xs text-[#687482]">Attendance</p>
                <p className="text-lg font-bold">{selectedProfile.student.attendance_pct}%</p>
              </div>
              <div className="p-3 rounded-xl bg-[#FFF1F5]">
                <p className="text-xs text-[#687482]">Prev. Score</p>
                <p className="text-lg font-bold">{selectedProfile.student.previous_term_score ?? "Restricted"}</p>
              </div>
              <div className="p-3 rounded-xl bg-[#FFF1F5]">
                <p className="text-xs text-[#687482]">Distance</p>
                <p className="text-lg font-bold">{selectedProfile.student.distance_km} km</p>
              </div>
            </div>

            {user?.role !== "outreach" && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-[#28313B]">Teacher Coordinator Observations</label>
                <textarea
                  rows={3}
                  value={obsInput}
                  onChange={(e) => setObsInput(e.target.value)}
                  className="w-full p-3 rounded-xl border border-[#F3DCE3] text-sm"
                />
                <button
                  onClick={saveObservations}
                  disabled={savingObs}
                  className="px-4 py-2 rounded-xl bg-[#D97998] text-white text-xs font-semibold"
                >
                  {savingObs ? "Saving..." : "Save Observation"}
                </button>
              </div>
            )}

            <div>
              <h3 className="text-sm font-bold text-[#28313B] mb-2">Risk Assessment History</h3>
              <div className="space-y-2">
                {selectedProfile.risk_history.map((r: any) => (
                  <div key={r.id} className="p-3 rounded-xl border border-[#F3DCE3] text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold">
                        v{r.version} • Score {r.priority_score}/100
                      </span>
                      <div className="flex items-center gap-2">
                        <PriorityBadge band={r.effective_band} />
                        <StatusBadge status={r.validation_status} />
                      </div>
                    </div>
                    <p className="text-[#687482]">{r.recommended_next_step}</p>
                    {r.override_reason && (
                      <p className="text-[#C05D7E] font-medium">Review note: {r.override_reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-[#28313B] mb-2">Intervention Timeline</h3>
              <div className="space-y-2">
                {selectedProfile.interventions.length === 0 ? (
                  <p className="text-xs text-[#687482]">No interventions logged yet.</p>
                ) : (
                  selectedProfile.interventions.map((iv: any) => (
                    <div key={iv.id} className="p-3 rounded-xl border border-[#F3DCE3] text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold">
                          #{iv.id} • {iv.intervention_type} ({iv.scheduled_date})
                        </span>
                        <StatusBadge status={iv.status} />
                      </div>
                      <p className="text-[#687482]">Worker: {iv.worker_name || iv.worker_id || "Unassigned"}</p>
                      {iv.outcomes.map((o: any) => (
                        <div key={o.id} className="mt-1 p-2 rounded-lg bg-[#E8F5EC] text-[#28313B]">
                          Outcome: <strong>{o.outcome_category}</strong> — {o.agreed_next_step}
                        </div>
                      ))}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
