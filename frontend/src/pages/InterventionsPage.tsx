import React, { useEffect, useState } from "react";
import { CheckCircle2, ClipboardPlus, CloudUpload, FilePlus2, WifiOff } from "lucide-react";
import api from "../lib/api";
import { Card, LoadingSkeleton, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";

const DRAFT_STORAGE_KEY = "shikshasetu_offline_drafts";

export const InterventionsPage: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");

  // Create intervention modal state
  const [showCreate, setShowCreate] = useState(false);
  const [newStudentId, setNewStudentId] = useState("ST009");
  const [newSchoolId, setNewSchoolId] = useState(7);
  const [newWorkerId, setNewWorkerId] = useState("OW04");
  const [newType, setNewType] = useState("Household Visit");
  const [newDate, setNewDate] = useState(new Date().toISOString().split("T")[0]);
  const [newNotes, setNewNotes] = useState("");

  // Outcome modal state
  const [outcomeTarget, setOutcomeTarget] = useState<any>(null);
  const [outcomeCat, setOutcomeCat] = useState("Contacted - Support Plan Agreed");
  const [visitCompleted, setVisitCompleted] = useState(true);
  const [agreedNextStep, setAgreedNextStep] = useState("");
  const [followUpReq, setFollowUpReq] = useState(false);
  const [followUpDate, setFollowUpDate] = useState("");
  const [subAtt, setSubAtt] = useState("");
  const [outcomeNotes, setOutcomeNotes] = useState("");

  // Offline drafts
  const [drafts, setDrafts] = useState<any[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(DRAFT_STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  });

  const loadInterventions = () => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    api
      .get("/api/interventions", { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadInterventions();
  }, [statusFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setFeedback("");
    try {
      await api.post("/api/interventions", {
        student_id: newStudentId,
        school_id: Number(newSchoolId),
        worker_id: newWorkerId || null,
        intervention_type: newType,
        scheduled_date: newDate,
        teacher_notes: newNotes,
      });
      setFeedback("Intervention scheduled and approved.");
      setShowCreate(false);
      setNewNotes("");
      loadInterventions();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create intervention.");
    }
  };

  const handleStatusChange = async (id: number, status: string) => {
    await api.patch(`/api/interventions/${id}/status`, { status });
    setFeedback(`Intervention #${id} marked as ${status}.`);
    loadInterventions();
  };

  const handleOutcomeSubmit = async (e: React.FormEvent, saveOffline = false) => {
    e.preventDefault();
    if (!outcomeTarget) return;

    const payload = {
      outcome_category: outcomeCat,
      visit_completed: visitCompleted,
      agreed_next_step: agreedNextStep,
      follow_up_required: followUpReq,
      follow_up_date: followUpDate || null,
      subsequent_attendance_pct: subAtt ? Number(subAtt) : null,
      notes: outcomeNotes,
    };

    if (saveOffline || !navigator.onLine) {
      const updated = [
        ...drafts,
        {
          ...payload,
          local_draft_id: `draft-${Date.now()}`,
          intervention_id: outcomeTarget.id,
          captured_at: new Date().toISOString(),
        },
      ];
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(updated));
      setDrafts(updated);
      setFeedback("Saved field outcome as a local offline draft. Sync when online.");
      setOutcomeTarget(null);
      return;
    }

    await api.post(`/api/interventions/${outcomeTarget.id}/outcome`, payload);
    setFeedback(`Outcome recorded for Intervention #${outcomeTarget.id}.`);
    setOutcomeTarget(null);
    setAgreedNextStep("");
    setOutcomeNotes("");
    loadInterventions();
  };

  const syncOfflineDrafts = async () => {
    if (drafts.length === 0) return;
    const res = await api.post("/api/interventions/sync-offline-drafts", { drafts });
    localStorage.setItem(DRAFT_STORAGE_KEY, "[]");
    setDrafts([]);
    setFeedback(`Synchronized ${res.data.synced_draft_ids.length} offline draft(s) to server.`);
    loadInterventions();
  };

  if (loading && !data) return <LoadingSkeleton rows={5} />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Intervention Lifecycle & Field Outcomes</h1>
          <p className="text-sm text-[#687482]">
            Schedule visits, update statuses, document standardized outcomes, and capture offline field drafts.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {drafts.length > 0 && (
            <button
              onClick={syncOfflineDrafts}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold"
            >
              <CloudUpload className="w-4 h-4" /> Sync {drafts.length} Offline Draft(s)
            </button>
          )}
          {(user?.role === "admin" || user?.role === "teacher") && (
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#D97998] hover:bg-[#C05D7E] text-white text-xs font-semibold"
            >
              <FilePlus2 className="w-4 h-4" /> New Intervention
            </button>
          )}
        </div>
      </div>

      {feedback && (
        <div className="p-3 rounded-xl bg-[#E8F5EC] border border-[#CBE7D4] text-xs font-medium text-[#3B7F60] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {feedback}
        </div>
      )}
      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">{error}</div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap gap-2">
        {["", "pending", "completed", "rescheduled", "cancelled"].map((st) => (
          <button
            key={st || "all"}
            onClick={() => setStatusFilter(st)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold capitalize border ${
              statusFilter === st
                ? "bg-[#D97998] text-white border-[#D97998]"
                : "bg-white text-[#687482] border-[#F3DCE3]"
            }`}
          >
            {st || "All"}
          </button>
        ))}
      </div>

      {/* Interventions Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#FFF1F5] text-xs text-[#687482] uppercase">
              <tr>
                <th className="px-4 py-3 text-left">ID / Student</th>
                <th className="px-4 py-3 text-left">Type & Date</th>
                <th className="px-4 py-3 text-left">Worker</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Attendance (Pre → Post)</th>
                <th className="px-4 py-3 text-left">Outcome</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F3DCE3]">
              {data?.interventions.map((iv: any) => (
                <tr key={iv.id} className="hover:bg-[#FFF9FB]">
                  <td className="px-4 py-3">
                    <p className="font-bold text-[#28313B]">
                      #{iv.id} • {iv.student_id}
                    </p>
                    <p className="text-[11px] text-[#687482]">School {iv.school_id}</p>
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <p className="font-semibold">{iv.intervention_type}</p>
                    <p className="text-[#687482]">{iv.scheduled_date}</p>
                  </td>
                  <td className="px-4 py-3 text-xs">{iv.worker_name || iv.worker_id || "—"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={iv.status} />
                  </td>
                  <td className="px-4 py-3 text-xs font-medium">
                    {iv.pre_attendance_pct ?? "—"}% → {iv.post_attendance_pct ?? "—"}%
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {iv.outcomes.length > 0 ? (
                      <span className="text-[#3B7F60] font-semibold">{iv.outcomes[0].outcome_category}</span>
                    ) : (
                      <span className="text-amber-700 font-medium">Outcome Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="inline-flex items-center gap-1.5">
                      <button
                        onClick={() => setOutcomeTarget(iv)}
                        className="px-2.5 py-1 rounded-lg bg-[#FFF1F5] text-[#C05D7E] text-xs font-semibold inline-flex items-center gap-1"
                      >
                        <ClipboardPlus className="w-3.5 h-3.5" /> Record Outcome
                      </button>
                      {iv.status === "pending" && (
                        <button
                          onClick={() => handleStatusChange(iv.id, "cancelled")}
                          className="px-2 py-1 rounded-lg border border-[#F3DCE3] text-xs text-[#687482]"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Create Intervention Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
          <form onSubmit={handleCreate} className="bg-white rounded-2xl border border-[#F3DCE3] max-w-md w-full p-6 space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-[#28313B]">Schedule Approved Intervention</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Student ID</label>
                <input
                  value={newStudentId}
                  onChange={(e) => setNewStudentId(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">School ID</label>
                <input
                  type="number"
                  value={newSchoolId}
                  onChange={(e) => setNewSchoolId(Number(e.target.value))}
                  className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Outreach Worker</label>
                <select
                  value={newWorkerId}
                  onChange={(e) => setNewWorkerId(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm bg-white"
                >
                  {data?.workers.map((w: any) => (
                    <option key={w.id} value={w.id}>
                      {w.id} - {w.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold">Scheduled Date</label>
                <input
                  type="date"
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
                  required
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold">Intervention Type</label>
              <select
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm bg-white"
              >
                <option>Household Visit</option>
                <option>School Counseling</option>
                <option>Family Check-in</option>
                <option>Transport Support Review</option>
              </select>
            </div>
            <textarea
              rows={2}
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              placeholder="Teacher context notes..."
              className="w-full p-2.5 rounded-xl border border-[#F3DCE3] text-sm"
            />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-xl text-xs font-semibold text-[#687482]">
                Cancel
              </button>
              <button type="submit" className="px-4 py-2 rounded-xl bg-[#D97998] text-white text-xs font-semibold">
                Create Intervention
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Record Outcome Modal */}
      {outcomeTarget && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
          <form
            onSubmit={(e) => handleOutcomeSubmit(e, false)}
            className="bg-white rounded-2xl border border-[#F3DCE3] max-w-md w-full p-6 space-y-3.5 shadow-xl"
          >
            <h2 className="text-lg font-bold text-[#28313B]">
              Record Visit Outcome (#{outcomeTarget.id} • {outcomeTarget.student_id})
            </h2>
            <div>
              <label className="text-xs font-semibold">Outcome Category</label>
              <select
                value={outcomeCat}
                onChange={(e) => setOutcomeCat(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm bg-white"
              >
                <option>Contacted - Support Plan Agreed</option>
                <option>Attendance Stabilizing</option>
                <option>Transport Barrier Identified</option>
                <option>Family Unavailable</option>
                <option>Health/Financial Referral</option>
              </select>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <label className="flex items-center gap-1.5 font-medium">
                <input type="checkbox" checked={visitCompleted} onChange={(e) => setVisitCompleted(e.target.checked)} />
                Visit Completed
              </label>
              <label className="flex items-center gap-1.5 font-medium">
                <input type="checkbox" checked={followUpReq} onChange={(e) => setFollowUpReq(e.target.checked)} />
                Follow-up Required
              </label>
            </div>
            {followUpReq && (
              <div>
                <label className="text-xs font-semibold">Follow-up Date</label>
                <input
                  type="date"
                  value={followUpDate}
                  onChange={(e) => setFollowUpDate(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
                />
              </div>
            )}
            <div>
              <label className="text-xs font-semibold">Subsequent Observed Attendance % (Optional)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={subAtt}
                onChange={(e) => setSubAtt(e.target.value)}
                placeholder="e.g. 64"
                className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-semibold">Agreed Next Step</label>
              <input
                required
                minLength={3}
                value={agreedNextStep}
                onChange={(e) => setAgreedNextStep(e.target.value)}
                placeholder="e.g. Coordinate cycle-pool / morning school buddy"
                className="w-full mt-1 px-3 py-2 rounded-xl border border-[#F3DCE3] text-sm"
              />
            </div>
            <textarea
              rows={2}
              value={outcomeNotes}
              onChange={(e) => setOutcomeNotes(e.target.value)}
              placeholder="Field notes (respectful, minimal info)..."
              className="w-full p-2.5 rounded-xl border border-[#F3DCE3] text-sm"
            />
            <div className="flex flex-wrap justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setOutcomeTarget(null)}
                className="px-3 py-2 rounded-xl text-xs font-semibold text-[#687482]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={(e) => handleOutcomeSubmit(e as any, true)}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold"
              >
                <WifiOff className="w-3.5 h-3.5" /> Save Offline Draft
              </button>
              <button type="submit" className="px-4 py-2 rounded-xl bg-[#D97998] text-white text-xs font-semibold">
                Save Outcome
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
