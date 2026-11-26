import React, { useEffect, useState } from "react";
import { Bot, Send, Shield, Sparkles, User as UserIcon } from "lucide-react";
import api from "../lib/api";
import { Card, DisclaimerBanner } from "../components/ui";

const QUICK_PROMPTS = [
  "Which students need attention this week?",
  "Why was ST009 prioritized?",
  "Which schools have the lowest attendance?",
  "Summarize the attendance performance of School 7.",
  "What follow-up actions are pending?",
  "What should a teacher review before a household visit?",
  "Summarize intervention outcomes.",
];

export const AssistantPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId] = useState("teacher-assistant-main");

  useEffect(() => {
    api.get("/api/assistant/status").then((res) => setStatus(res.data));
    api.get("/api/assistant/history", { params: { session_id: sessionId } }).then((res) => {
      setMessages(res.data.messages || []);
    });
  }, [sessionId]);

  const sendQuestion = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setSending(true);
    setQuestion("");

    const optimisticUser = { id: `tmp-${Date.now()}`, role: "user", content: trimmed };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      const res = await api.post("/api/assistant/ask", {
        question: trimmed,
        session_id: sessionId,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-${Date.now()}`,
          role: "assistant",
          content: res.data.reply,
          provider_used: res.data.provider_used,
          verified_facts: res.data.verified_facts,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: err.response?.data?.detail || "Unable to reach AI assistant backend.",
          provider_used: "error",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Grounded AI Teacher Assistant</h1>
          <p className="text-sm text-[#687482]">
            Retrieves verified backend facts first, computes numbers in Python, and protects student privacy.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border bg-white border-[#F3DCE3]">
          <Shield className="w-3.5 h-3.5 text-[#4D9B78]" />
          {status?.gemini_configured
            ? `Gemini Connected (${status.model})`
            : "Grounded Backend Fallback (Add GEMINI_API_KEY in backend/.env)"}
        </div>
      </div>

      <DisclaimerBanner title="PII-Safe & Human-in-the-Loop AI Architecture">
        The assistant never invents student records, never assigns risk scores independently, and strips personal
        names/contacts before sending structured statistics to Gemini. Teachers review every suggestion.
      </DisclaimerBanner>

      {/* Quick Prompts */}
      <div className="flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((q) => (
          <button
            key={q}
            onClick={() => sendQuestion(q)}
            disabled={sending}
            className="px-3 py-1.5 rounded-full bg-[#FFF1F5] hover:bg-[#F6C9D5]/50 border border-[#F6C9D5] text-xs font-medium text-[#28313B] transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Window */}
      <Card className="flex flex-col h-[520px]">
        <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center text-[#687482] max-w-md mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-[#FFF1F5] border border-[#F6C9D5] flex items-center justify-center mb-3">
                <Sparkles className="w-6 h-6 text-[#D97998]" />
              </div>
              <p className="text-sm font-semibold text-[#28313B]">Ask about students, schools, or visit readiness</p>
              <p className="text-xs mt-1">
                Try clicking any suggested prompt above, e.g. <em>“Why was ST009 prioritized?”</em>
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-xl bg-[#FFF1F5] border border-[#F6C9D5] flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-[#D97998]" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
                  msg.role === "user"
                    ? "bg-[#D97998] text-white"
                    : "bg-[#FFF9FB] border border-[#F3DCE3] text-[#28313B]"
                }`}
              >
                {msg.content}
                {msg.provider_used && (
                  <div className="mt-2 pt-2 border-t border-[#F3DCE3] text-[10px] text-[#687482] flex items-center justify-between">
                    <span>Engine: {msg.provider_used}</span>
                    <span>Facts grounded in authorized DB</span>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-xl bg-[#28313B] text-white flex items-center justify-center shrink-0">
                  <UserIcon className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex items-center gap-2 text-xs text-[#687482]">
              <Bot className="w-4 h-4 animate-bounce text-[#D97998]" />
              Querying verified database records & generating grounded explanation...
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendQuestion(question);
          }}
          className="p-4 border-t border-[#F3DCE3] flex gap-2.5 bg-white rounded-b-2xl"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a grounded question (e.g. Summarize attendance performance of School 7)..."
            className="flex-1 px-4 py-2.5 rounded-xl border border-[#F3DCE3] text-sm focus:outline-none focus:ring-2 focus:ring-[#F6C9D5]"
          />
          <button
            type="submit"
            disabled={sending || !question.trim()}
            className="px-4 py-2.5 rounded-xl bg-[#D97998] hover:bg-[#C05D7E] text-white text-sm font-semibold inline-flex items-center gap-2 disabled:opacity-50"
          >
            <Send className="w-4 h-4" /> Ask
          </button>
        </form>
      </Card>
    </div>
  );
};
