import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

export const AnimatedCounter: React.FC<{ value: number; suffix?: string; prefix?: string; decimals?: number }> = ({
  value,
  suffix = "",
  prefix = "",
  decimals = 0,
}) => {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let start = 0;
    const duration = 500;
    const steps = 20;
    const increment = value / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep += 1;
      start += increment;
      if (currentStep >= steps) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(start);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value]);

  const formatted = decimals > 0 ? display.toFixed(decimals) : Math.round(display).toLocaleString("en-IN");
  return (
    <span>
      {prefix}
      {formatted}
      {suffix}
    </span>
  );
};

export const Card: React.FC<{
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}> = ({ children, className = "", hover = false }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
    whileHover={hover ? { y: -2, transition: { duration: 0.15 } } : undefined}
    className={`bg-white rounded-2xl border border-[#F3DCE3] shadow-card ${className}`}
  >
    {children}
  </motion.div>
);

export const PriorityBadge: React.FC<{ band: string }> = ({ band }) => {
  if (band === "High Priority") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
        <AlertCircle className="w-3.5 h-3.5" />
        High Priority
      </span>
    );
  }
  if (band === "Review Soon") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
        <Info className="w-3.5 h-3.5" />
        Review Soon
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#E8F5EC] text-[#3B7F60] border border-[#CBE7D4]">
      <CheckCircle2 className="w-3.5 h-3.5" />
      Routine Review
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const s = status.toLowerCase();
  const styles: Record<string, string> = {
    completed: "bg-[#E8F5EC] text-[#3B7F60] border-[#CBE7D4]",
    approved: "bg-[#E8F5EC] text-[#3B7F60] border-[#CBE7D4]",
    validated: "bg-[#E8F5EC] text-[#3B7F60] border-[#CBE7D4]",
    pending: "bg-[#FFF1F5] text-[#B85275] border-[#F6C9D5]",
    pending_review: "bg-[#FFF1F5] text-[#B85275] border-[#F6C9D5]",
    proposed: "bg-amber-50 text-amber-800 border-amber-200",
    rescheduled: "bg-amber-50 text-amber-800 border-amber-200",
    overridden: "bg-indigo-50 text-indigo-700 border-indigo-200",
    cancelled: "bg-slate-100 text-slate-600 border-slate-200",
    rejected: "bg-slate-100 text-slate-600 border-slate-200",
  };
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize ${
        styles[s] || "bg-slate-50 text-slate-700 border-slate-200"
      }`}
    >
      {status.replace("_", " ")}
    </span>
  );
};

export const DisclaimerBanner: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="bg-[#FFF1F5] border border-[#F6C9D5] rounded-xl p-3.5 flex items-start gap-3 text-sm text-[#28313B]">
    <Info className="w-5 h-5 text-[#D97998] shrink-0 mt-0.5" />
    <div>
      <p className="font-semibold text-[#28313B]">{title}</p>
      <p className="text-[#687482] text-xs mt-0.5 leading-relaxed">{children}</p>
    </div>
  </div>
);

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => (
  <div className="space-y-3 animate-pulse">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-14 bg-[#FFF1F5] rounded-xl border border-[#F6C9D5]/40" />
    ))}
  </div>
);
