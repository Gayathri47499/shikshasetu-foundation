import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Info, RefreshCw, ShieldCheck, SlidersHorizontal } from "lucide-react";
import api from "../lib/api";
import { Card, DisclaimerBanner, LoadingSkeleton, PriorityBadge, StatusBadge } from "../components/ui";

export const RiskIntelligencePage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);

  // Override / Validation form
  const [decision, setDecision] = useState<"validated" | "overridden" | "deferred">("validated");
  const [overrideBand, setOverrideBand] = useState("Review Soon");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState("");

  const loadQueue = () => {
    setLoading(true);
    api
      .get("/api/risk/review-queue")
      .then((res) => {
        setData(res.data);
        if (res.data.queue.length > 0 && !selected) {
          setSelected(res.data.queue[0]);
        } else if (selected) {
          const updated = res.data.queue.find((q: any) => q.student_id === selected.student_id);
          if (updated) setSelected(updated);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleRecalculate = async () => {
    setRecalculating(true);
    setFeedback("");
    try {
      const res = await api.post("/api/risk/recalculate");
      setFeedback(res.data.message);
      loadQueue();
    } finally {
      setRecalculating(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    setSubmitting(true);
    setFeedback("");
    try {
      const res = await api.post(`/api/risk/${selected.student_id}/review`, {
        validation_status: decision,
        effective_band: decision === "overridden" ? overrideBand : undefined,
        override_reason: reason,
      });
      setFeedback(res.data.message);
      setReason("");
      loadQueue();
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !data) return <LoadingSkeleton rows={6} />;
  if (!data) return null;

  const { queue, scoring_config, methodology_disclaimer } = data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Explainable Student Risk Intelligence</h1>
          <p className="text-sm text-[#687482]">
            Transparent rule-based operational triage with missing-data visibility and teacher override control.
          </p>
        </div>
        <button
          onClick={handleRecalculate}
          disabled={recalculating}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#D97998] hover:bg-[#C05D7E] text-white text-sm font-semibold disabled:opacity-60"
        >
          <RefreshCw className={`w-4 h-4 ${recalculating ? "animate-spin" : ""}`} />
          Recalculate Indicators
        </button>
      </div>

      <DisclaimerBanner title="Responsible AI Boundary: Operational Review Index (Not a Dropout Classifier)">
        {methodology_disclaimer} Weights (Design Assumptions): Attendance ({scoring_config.attendance_max_weight} pts) +
        Academic ({scoring_config.academic_max_weight} pts) + Distance/Access ({scoring_config.distance_max_weight} pts) +
        Pending Outcome Follow-up ({scoring_config.followup_max_weight} pts). Prior visits alone never penalize a student.
      </DisclaimerBanner>

      {feedback && (
        <div className="p-3 rounded-xl bg-[#E8F5EC] border border-[#CBE7D4] text-xs font-medium text-[#3B7F60] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          {feedback}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Priority Queue Table */}
        <Card className="lg:col-span-7 overflow-hidden">
          <div className="p-4 border-b border-[#F3DCE3] flex items-center justify-between">
            <h2 className="font-bold text-base">Prioritized Review Queue ({queue.length} Students)</h2>
            <span className="text-xs text-[#687482]">Click a row for full explainability</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#FFF1F5] text-xs text-[#687482] uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Student</th>
                  <th className="px-4 py-3 text-right">Score</th>
                  <th className="px-4 py-3 text-right">Att.</th>
                  <th className="px-4 py-3 text-right">Prev.</th>
                  <th className="px-4 py-3 text-right">Dist.</th>
                  <th className="px-4 py-3 text-left">Priority Band</th>
                  <th className="px-4 py-3 text-left">Validation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3DCE3]">
                {queue.map((item: any) => (
                  <tr
                    key={item.student_id}
                    onClick={() => setSelected(item)}
                    className={`cursor-pointer transition-colors ${
                      selected?.student_id === item.student_id ? "bg-[#FFF1F5]" : "hover:bg-[#FFF9FB]"
                    }`}
                  >
                    <td className="px-4 py-3">
                      <p className="font-bold text-[#28313B]">{item.student_id}</p>
                      <p className="text-[11px] text-[#687482]">{item.school_name}</p>
                    </td>
                    <td className="px-4 py-3 text-right font-extrabold text-[#D97998]">{item.priority_score}</td>
                    <td className="px-4 py-3 text-right">{item.attendance_pct}%</td>
                    <td className="px-4 py-3 text-right">{item.previous_term_score ?? "—"}</td>
                    <td className="px-4 py-3 text-right">{item.distance_km} km</td>
                    <td className="px-4 py-3">
                      <PriorityBadge band={item.effective_band} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={item.validation_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Explainability & Teacher Override Panel */}
        <Card className="lg:col-span-5 p-5 space-y-5">
          {selected ? (
            <>
              <div className="flex items-start justify-between border-b border-[#F3DCE3] pb-4">
                <div>
                  <span className="text-xs font-semibold text-[#D97998]">
                    Explainability Panel • {selected.school_name}
                  </span>
                  <h3 className="text-xl font-bold text-[#28313B]">
                    {selected.student_id} — {selected.priority_score}/100
                  </h3>
                  <div className="flex items-center gap-2 mt-2">
                    <PriorityBadge band={selected.effective_band} />
                    <StatusBadge status={selected.validation_status} />
                  </div>
                </div>
                <SlidersHorizontal className="w-5 h-5 text-[#D97998]" />
              </div>

              {/* Factor Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wide text-[#687482]">
                  Contributing Indicators & Cautions
                </h4>
                {selected.contributing_factors.map((f: any) => {
                  const pct = Math.min(100, (f.points / f.max_points) * 100);
                  return (
                    <div key={f.factor} className="p-3 rounded-xl bg-[#FFF9FB] border border-[#F3DCE3] space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span>
                          {f.factor} ({f.value_display})
                        </span>
                        <span className="text-[#C05D7E]">
                          {f.points} / {f.max_points} pts
                        </span>
                      </div>
                      <div className="w-full h-2 bg-white rounded-full overflow-hidden border border-[#F3DCE3]">
                        <div className="h-full bg-[#D97998] rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <p className="text-xs text-[#28313B]">{f.explanation}</p>
                      <p className="text-[11px] text-[#687482] italic">Caution: {f.caution}</p>
                    </div>
                  );
                })}
              </div>

              {/* Missing Information */}
              <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 space-y-1">
                <p className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" /> Missing Information & Data Gaps
                </p>
                <ul className="list-disc pl-5 text-xs text-amber-800 space-y-0.5">
                  {selected.missing_data_flags.map((m: string, idx: number) => (
                    <li key={idx}>{m}</li>
                  ))}
                </ul>
              </div>

              {/* Recommended Next Step */}
              <div className="p-3.5 rounded-xl bg-[#E8F5EC] border border-[#CBE7D4] text-xs text-[#28313B]">
                <p className="font-bold text-[#3B7F60] flex items-center gap-1.5">
                  <Info className="w-4 h-4" /> Recommended Next Step
                </p>
                <p className="mt-1">{selected.recommended_next_step}</p>
              </div>

              {/* Teacher Validation / Override Form */}
              <form onSubmit={handleReviewSubmit} className="pt-3 border-t border-[#F3DCE3] space-y-3">
                <h4 className="text-xs font-bold text-[#28313B] flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#D97998]" />
                  Teacher Review & Override (Audit Logged)
                </h4>

                <div className="grid grid-cols-3 gap-2">
                  {(["validated", "overridden", "deferred"] as const).map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setDecision(opt)}
                      className={`py-2 px-2 rounded-xl text-xs font-semibold capitalize border ${
                        decision === opt
                          ? "bg-[#D97998] text-white border-[#D97998]"
                          : "bg-white text-[#687482] border-[#F3DCE3]"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>

                {decision === "overridden" && (
                  <select
                    value={overrideBand}
                    onChange={(e) => setOverrideBand(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#F3DCE3] text-xs bg-white"
                  >
                    <option value="High Priority">High Priority</option>
                    <option value="Review Soon">Review Soon</option>
                    <option value="Routine Review">Routine Review</option>
                  </select>
                )}

                <textarea
                  required
                  minLength={3}
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Document educator review reason (e.g. verified family travel schedule)..."
                  className="w-full p-2.5 rounded-xl border border-[#F3DCE3] text-xs"
                />

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 rounded-xl bg-[#28313B] hover:bg-[#1a2027] text-white text-xs font-semibold disabled:opacity-60"
                >
                  {submitting ? "Recording..." : "Submit Educator Decision"}
                </button>
              </form>
            </>
          ) : null}
        </Card>
      </div>
    </div>
  );
};
