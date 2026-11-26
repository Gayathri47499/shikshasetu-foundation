import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, GraduationCap, KeyRound, Lock, Mail, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { SchoolHeroIllustration } from "../components/Illustrations";
import api from "../lib/api";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("admin@shikshasetu.org");
  const [password, setPassword] = useState("Admin@123");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Forgot password state
  const [forgotMode, setForgotMode] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [devResetToken, setDevResetToken] = useState("");
  const [resetTokenInput, setResetTokenInput] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetMessage, setResetMessage] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Unable to sign in. Check credentials and backend server.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setResetMessage("");
    try {
      const res = await api.post("/api/auth/forgot-password", { email: resetEmail });
      setResetMessage(res.data.message);
      if (res.data.dev_reset_token) {
        setDevResetToken(res.data.dev_reset_token);
        setResetTokenInput(res.data.dev_reset_token);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Could not process reset request.");
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await api.post("/api/auth/reset-password", {
        token: resetTokenInput,
        new_password: newPassword,
      });
      setResetMessage(res.data.message);
      setForgotMode(false);
      setPassword(newPassword);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Reset failed.");
    }
  };

  const quickFill = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setError("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FFF1F5] via-white to-[#FFF9FB] flex items-center justify-center p-4 lg:p-8">
      <div className="max-w-5xl w-full grid lg:grid-cols-2 bg-white rounded-3xl border border-[#F3DCE3] shadow-soft overflow-hidden">
        {/* Left Hero Column */}
        <div className="bg-[#FFF1F5] p-8 lg:p-10 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[#F3DCE3]">
          <div>
            <div className="inline-flex items-center gap-2.5 bg-white px-3.5 py-2 rounded-2xl border border-[#F6C9D5] shadow-sm">
              <GraduationCap className="w-6 h-6 text-[#D97998]" />
              <div>
                <p className="text-sm font-bold text-[#28313B] leading-none">ShikshaSetu Foundation</p>
                <p className="text-[11px] text-[#687482] mt-0.5">Student Success & Intervention Intelligence</p>
              </div>
            </div>

            <motion.h1
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-2xl lg:text-3xl font-extrabold text-[#28313B] mt-6 leading-tight"
            >
              Every Student Matters.
              <span className="block text-[#D97998]">Every Opportunity Counts.</span>
            </motion.h1>
            <p className="text-sm text-[#687482] mt-3 leading-relaxed">
              Explainable student attendance triage, capacity-constrained household outreach planning across 10 schools,
              and grounded AI teacher assistance.
            </p>
          </div>

          <div className="my-6 flex justify-center">
            <SchoolHeroIllustration className="w-full max-w-sm" />
          </div>

          <div className="grid grid-cols-3 gap-2.5 text-center">
            <div className="bg-white/90 rounded-xl p-2.5 border border-[#F6C9D5]">
              <p className="text-lg font-bold text-[#28313B]">10</p>
              <p className="text-[11px] text-[#687482]">Schools</p>
            </div>
            <div className="bg-white/90 rounded-xl p-2.5 border border-[#F6C9D5]">
              <p className="text-lg font-bold text-[#28313B]">900</p>
              <p className="text-[11px] text-[#687482]">Students</p>
            </div>
            <div className="bg-white/90 rounded-xl p-2.5 border border-[#F6C9D5]">
              <p className="text-lg font-bold text-[#4D9B78]">100/wk</p>
              <p className="text-[11px] text-[#687482]">Visit Cap</p>
            </div>
          </div>
        </div>

        {/* Right Auth Column */}
        <div className="p-8 lg:p-10 flex flex-col justify-center">
          {!forgotMode ? (
            <>
              <div className="mb-6">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#C05D7E] bg-[#FFF1F5] px-3 py-1 rounded-full border border-[#F6C9D5]">
                  <Sparkles className="w-3.5 h-3.5" />
                  Role-Based Secure Sign In
                </span>
                <h2 className="text-2xl font-bold text-[#28313B] mt-3">Welcome back</h2>
                <p className="text-sm text-[#687482]">Sign in with your Foundation, Coordinator, or Outreach account.</p>
              </div>

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
                  {error}
                </div>
              )}
              {resetMessage && (
                <div className="mb-4 p-3 rounded-xl bg-[#E8F5EC] border border-[#CBE7D4] text-xs text-[#3B7F60] flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  {resetMessage}
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#28313B] mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-[#687482] absolute left-3.5 top-3" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#F3DCE3] text-sm focus:outline-none focus:ring-2 focus:ring-[#F6C9D5]"
                      placeholder="name@shikshasetu.org"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-semibold text-[#28313B]">Password</label>
                    <button
                      type="button"
                      onClick={() => {
                        setForgotMode(true);
                        setResetEmail(email);
                        setError("");
                      }}
                      className="text-xs font-medium text-[#D97998] hover:underline"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-[#687482] absolute left-3.5 top-3" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#F3DCE3] text-sm focus:outline-none focus:ring-2 focus:ring-[#F6C9D5]"
                      placeholder="Enter password"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 px-4 rounded-xl bg-[#D97998] hover:bg-[#C05D7E] text-white font-semibold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
                >
                  {submitting ? "Signing in..." : "Sign In to Platform"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>

              {/* Demo role selector for evaluation */}
              <div className="mt-6 pt-5 border-t border-[#F3DCE3]">
                <p className="text-xs font-semibold text-[#687482] mb-2.5">
                  Assessment Role Quick-Fill (Real Backend JWT Auth):
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => quickFill("admin@shikshasetu.org", "Admin@123")}
                    className="p-2.5 rounded-xl border border-[#F3DCE3] hover:bg-[#FFF1F5] text-left transition-colors"
                  >
                    <p className="text-xs font-bold text-[#28313B]">Foundation Admin</p>
                    <p className="text-[10px] text-[#687482] truncate">All 10 schools & CSV</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => quickFill("teacher.school7@shikshasetu.org", "Teacher@123")}
                    className="p-2.5 rounded-xl border border-[#F3DCE3] hover:bg-[#FFF1F5] text-left transition-colors"
                  >
                    <p className="text-xs font-bold text-[#28313B]">Teacher (School 7)</p>
                    <p className="text-[10px] text-[#687482] truncate">Review & override</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => quickFill("outreach.ow04@shikshasetu.org", "Outreach@123")}
                    className="p-2.5 rounded-xl border border-[#F3DCE3] hover:bg-[#FFF1F5] text-left transition-colors"
                  >
                    <p className="text-xs font-bold text-[#28313B]">Outreach (OW04)</p>
                    <p className="text-[10px] text-[#687482] truncate">Assigned visits</p>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-[#28313B] flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-[#D97998]" />
                Reset Password
              </h2>
              {error && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">{error}</div>
              )}
              {resetMessage && (
                <div className="p-3 rounded-xl bg-[#FFF1F5] border border-[#F6C9D5] text-xs text-[#28313B]">
                  {resetMessage}
                  {devResetToken && (
                    <p className="mt-1 font-mono text-[11px] break-all text-[#C05D7E]">
                      Dev Reset Token: {devResetToken}
                    </p>
                  )}
                </div>
              )}
              <form onSubmit={handleRequestReset} className="space-y-3">
                <input
                  type="email"
                  required
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[#F3DCE3] text-sm"
                  placeholder="Enter your account email"
                />
                <button
                  type="submit"
                  className="w-full py-2 rounded-xl bg-[#FFF1F5] border border-[#F6C9D5] text-[#C05D7E] font-semibold text-sm"
                >
                  Generate Reset Token
                </button>
              </form>

              {devResetToken && (
                <form onSubmit={handleConfirmReset} className="space-y-3 pt-3 border-t border-[#F3DCE3]">
                  <input
                    type="text"
                    required
                    value={resetTokenInput}
                    onChange={(e) => setResetTokenInput(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#F3DCE3] text-xs font-mono"
                    placeholder="Paste reset token"
                  />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-[#F3DCE3] text-sm"
                    placeholder="New password (min 6 chars)"
                  />
                  <button
                    type="submit"
                    className="w-full py-2.5 rounded-xl bg-[#D97998] text-white font-semibold text-sm"
                  >
                    Save New Password
                  </button>
                </form>
              )}

              <button
                type="button"
                onClick={() => setForgotMode(false)}
                className="text-xs font-semibold text-[#687482] hover:text-[#28313B]"
              >
                ← Back to Sign In
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
