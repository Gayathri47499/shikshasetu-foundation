import React, { useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import api from "../lib/api";
import { Card, DisclaimerBanner, LoadingSkeleton } from "../components/ui";

export const ImpactReportsPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [schoolId, setSchoolId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const fetchImpact = () => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (schoolId) params.school_id = schoolId;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    api
      .get("/api/reports/impact", { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchImpact();
  }, [schoolId, dateFrom, dateTo]);

  const downloadFile = async (type: "pdf" | "csv") => {
    const params: Record<string, string> = {};
    if (schoolId) params.school_id = schoolId;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    const res = await api.get(`/api/reports/impact/${type}`, {
      params,
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      type === "pdf" ? "shikshasetu_impact_report.pdf" : "shikshasetu_impact_kpis.csv"
    );
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (loading && !data) return <LoadingSkeleton rows={5} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Foundation Social Impact Reports</h1>
          <p className="text-sm text-[#687482]">
            8 Core Measurable Indicators and 90-Day Pilot Measurement Framework (Challenge A Task F).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={schoolId}
            onChange={(e) => setSchoolId(e.target.value)}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-xs bg-white"
          >
            <option value="">All Schools</option>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
              <option key={n} value={n}>
                School {n}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-xs bg-white"
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="px-3 py-2 rounded-xl border border-[#F3DCE3] text-xs bg-white"
          />
          <button
            onClick={() => downloadFile("csv")}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-[#F6C9D5] text-xs font-semibold text-[#C05D7E]"
          >
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <button
            onClick={() => downloadFile("pdf")}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#D97998] hover:bg-[#C05D7E] text-white text-xs font-semibold"
          >
            <FileText className="w-4 h-4" /> Download PDF Report
          </button>
        </div>
      </div>

      <DisclaimerBanner title="Measurement Integrity Notice">
        {data.causal_disclaimer}
      </DisclaimerBanner>

      {/* 8 Impact KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {data.kpis.map((kpi: any) => (
          <Card key={kpi.id} hover className="p-5 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[#FFF1F5] text-[#C05D7E]">
                {kpi.data_label}
              </span>
              <h3 className="text-sm font-bold text-[#28313B] mt-2.5">{kpi.name}</h3>
              <p className="text-2xl font-extrabold text-[#D97998] mt-1">{kpi.value}</p>
            </div>
            <p className="text-xs text-[#687482] mt-3 leading-relaxed">{kpi.definition}</p>
          </Card>
        ))}
      </div>

      {/* 90-Day Measurement Design */}
      <Card className="p-6">
        <h2 className="font-bold text-base text-[#28313B] mb-4">90-Day Impact Measurement Plan</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.ninety_day_plan.map((phase: any) => (
            <div key={phase.phase} className="p-4 rounded-2xl bg-[#FFF9FB] border border-[#F3DCE3] space-y-2">
              <p className="text-sm font-bold text-[#C05D7E]">{phase.phase}</p>
              <p className="text-xs text-[#28313B] leading-relaxed">{phase.activities}</p>
              <p className="text-[11px] text-[#4D9B78] font-semibold pt-1">Evidence: {phase.evidence}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
