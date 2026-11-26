import React, { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../lib/api";
import { Card, DisclaimerBanner, LoadingSkeleton } from "../components/ui";
import { CommunityOutreachIllustration, EmptyStateBooksIllustration } from "../components/Illustrations";

export const OutcomesPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/reports/impact")
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton rows={4} />;
  if (!data) return null;

  const { outcome_analytics, causal_disclaimer } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Intervention Outcome Analytics</h1>
          <p className="text-sm text-[#687482]">
            Track visit completion, pending follow-ups, and descriptive attendance changes before vs. after support.
          </p>
        </div>
        <CommunityOutreachIllustration className="w-28 h-20 hidden sm:block" />
      </div>

      <DisclaimerBanner title="Correlation vs. Causation Safeguard">
        {causal_disclaimer}
      </DisclaimerBanner>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Completed</p>
          <p className="text-2xl font-extrabold text-[#4D9B78] mt-1">{outcome_analytics.completed}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Pending / Rescheduled</p>
          <p className="text-2xl font-extrabold text-[#D97998] mt-1">{outcome_analytics.pending}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Follow-ups Due</p>
          <p className="text-2xl font-extrabold text-amber-600 mt-1">{outcome_analytics.followups_due}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Improved Attendance</p>
          <p className="text-2xl font-extrabold text-[#4D9B78] mt-1">{outcome_analytics.improved_attendance_count}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[#687482] font-semibold">Needs Additional Review</p>
          <p className="text-2xl font-extrabold text-[#28313B] mt-1">
            {outcome_analytics.requires_additional_review_count}
          </p>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="font-bold text-base text-[#28313B] mb-1">Attendance Before vs. After Recorded Intervention</h2>
        <p className="text-xs text-[#687482] mb-4">
          Updates live whenever a post-visit attendance observation is logged in Intervention Lifecycle.
        </p>

        {outcome_analytics.before_after_series.length === 0 ? (
          <div className="py-10 flex flex-col items-center text-center">
            <EmptyStateBooksIllustration />
            <p className="text-sm font-semibold text-[#28313B] mt-2">
              No post-intervention attendance measurements recorded yet
            </p>
            <p className="text-xs text-[#687482] max-w-md mt-1">
              Go to <strong>Intervention Lifecycle</strong> and click <strong>Record Outcome</strong> with a subsequent
              attendance percentage to visualize descriptive before/after comparisons here.
            </p>
          </div>
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={outcome_analytics.before_after_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3DCE3" />
                <XAxis dataKey="student_id" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="pre_attendance_pct" name="Pre-Intervention %" fill="#F6C9D5" radius={[6, 6, 0, 0]} />
                <Bar dataKey="post_attendance_pct" name="Post-Intervention %" fill="#4D9B78" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
    </div>
  );
};
