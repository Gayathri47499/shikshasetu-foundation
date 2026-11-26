import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet, Upload } from "lucide-react";
import api from "../lib/api";
import { Card, DisclaimerBanner, StatusBadge } from "../components/ui";

const ENTITY_OPTIONS = [
  { value: "students", label: "Students (id, school_id, attendance_pct, distance_km)" },
  { value: "schools", label: "Schools (id, name, enrolled_students, baseline_attendance_pct)" },
  { value: "attendance", label: "Attendance (student_id, school_id, week_label, record_date, attendance_pct)" },
  { value: "academics", label: "Academic Records (student_id, term, score)" },
  { value: "interventions", label: "Interventions (student_id, school_id, scheduled_date, intervention_type)" },
];

export const DataUploadPage: React.FC = () => {
  const [entityType, setEntityType] = useState("students");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadHistory = () => {
    api.get("/api/imports/history").then((res) => setHistory(res.data.batches || []));
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDownloadTemplate = async () => {
    const res = await api.get(`/api/imports/template/${entityType}`, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `template_${entityType}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handlePreview = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setMessage("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await api.post(`/api/imports/${entityType}/preview`, form);
      setPreview(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to validate CSV.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await api.post(`/api/imports/${entityType}/confirm`, form);
      setMessage(`Imported ${res.data.imported_count} valid row(s). ${res.data.validation.error_count} flagged row(s) excluded.`);
      setPreview(res.data.validation);
      loadHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Import failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">CSV Data Upload & Quality Validation</h1>
          <p className="text-sm text-[#687482]">
            Preview rows, catch missing fields, duplicates, invalid ranges, and missing IDs before committing.
          </p>
        </div>
        <button
          onClick={handleDownloadTemplate}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white border border-[#F6C9D5] text-xs font-semibold text-[#C05D7E]"
        >
          <Download className="w-4 h-4" /> Sample {entityType}.csv
        </button>
      </div>

      <DisclaimerBanner title="Zero Silent Drops Policy">
        Invalid rows are never silently discarded. Every schema error, duplicate ID, out-of-range attendance (&lt;0 or
        &gt;100), or unknown School/Student ID is displayed with exact row numbers for correction.
      </DisclaimerBanner>

      {message && (
        <div className="p-3 rounded-xl bg-[#E8F5EC] border border-[#CBE7D4] text-xs font-medium text-[#3B7F60] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {message}
        </div>
      )}
      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">{error}</div>
      )}

      <Card className="p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="text-xs font-semibold text-[#28313B]">Target Dataset</label>
            <select
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value);
                setPreview(null);
              }}
              className="w-full mt-1.5 px-3 py-2.5 rounded-xl border border-[#F3DCE3] text-sm bg-white"
            >
              {ENTITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-[#28313B]">Select CSV File</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                setFile(e.target.files?.[0] || null);
                setPreview(null);
              }}
              className="w-full mt-1.5 text-xs file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:bg-[#FFF1F5] file:text-[#C05D7E] file:font-semibold"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handlePreview}
              disabled={!file || loading}
              className="flex-1 py-2.5 px-4 rounded-xl bg-[#FFF1F5] border border-[#F6C9D5] text-[#C05D7E] text-xs font-semibold inline-flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" /> Validate Preview
            </button>
            {preview && preview.valid_count > 0 && (
              <button
                onClick={handleConfirmImport}
                disabled={loading}
                className="flex-1 py-2.5 px-4 rounded-xl bg-[#D97998] text-white text-xs font-semibold inline-flex items-center justify-center gap-1.5"
              >
                <Upload className="w-4 h-4" /> Import ({preview.valid_count})
              </button>
            )}
          </div>
        </div>
      </Card>

      {preview && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-5 space-y-3">
            <h2 className="font-bold text-base">
              Validation Summary: {preview.valid_count} Valid / {preview.error_count} Error(s)
            </h2>
            {preview.errors.length === 0 ? (
              <p className="text-xs text-[#4D9B78] font-medium">All rows passed validation checks.</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                {preview.errors.map((err: any, idx: number) => (
                  <div key={idx} className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <strong>Row {err.row} ({err.field}):</strong> {err.message}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-5 space-y-3">
            <h2 className="font-bold text-base">Upload Preview (First 25 Rows)</h2>
            <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar text-xs">
              {preview.preview_rows.map((r: any) => (
                <div
                  key={r.row}
                  className={`p-2.5 rounded-xl border ${
                    r.status === "valid" ? "bg-[#E8F5EC]/60 border-[#CBE7D4]" : "bg-rose-50 border-rose-200"
                  }`}
                >
                  <div className="flex justify-between font-semibold">
                    <span>Row {r.row}</span>
                    <span className="uppercase">{r.status}</span>
                  </div>
                  <p className="text-[#687482] font-mono text-[11px] truncate mt-0.5">{JSON.stringify(r.data)}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="p-4 border-b border-[#F3DCE3]">
          <h2 className="font-bold text-base">Recent Import Batches</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-[#FFF1F5] text-[#687482] uppercase">
              <tr>
                <th className="px-4 py-3 text-left">File</th>
                <th className="px-4 py-3 text-left">Dataset</th>
                <th className="px-4 py-3 text-right">Valid</th>
                <th className="px-4 py-3 text-right">Errors</th>
                <th className="px-4 py-3 text-left">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F3DCE3]">
              {history.map((b) => (
                <tr key={b.id}>
                  <td className="px-4 py-3 font-semibold">{b.filename}</td>
                  <td className="px-4 py-3 capitalize">{b.entity_type}</td>
                  <td className="px-4 py-3 text-right text-[#4D9B78] font-bold">{b.valid_rows}</td>
                  <td className="px-4 py-3 text-right text-rose-600 font-bold">{b.error_rows}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={b.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
