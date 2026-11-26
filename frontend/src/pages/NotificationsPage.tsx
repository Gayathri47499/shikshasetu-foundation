import React, { useEffect, useState } from "react";
import { Bell, CheckCheck } from "lucide-react";
import api from "../lib/api";
import { Card, LoadingSkeleton } from "../components/ui";

export const NotificationsPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .get("/api/notifications")
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const markRead = async (id: number) => {
    await api.post(`/api/notifications/${id}/read`);
    load();
  };

  const markAllRead = async () => {
    await api.post("/api/notifications/read-all");
    load();
  };

  if (loading && !data) return <LoadingSkeleton rows={4} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#28313B]">Notification Center</h1>
          <p className="text-sm text-[#687482]">
            Review alerts, pending validations, overdue follow-ups, and weekly operational summaries.
          </p>
        </div>
        <button
          onClick={markAllRead}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-[#F6C9D5] text-xs font-semibold text-[#C05D7E] hover:bg-[#FFF1F5]"
        >
          <CheckCheck className="w-4 h-4" /> Mark All Read
        </button>
      </div>

      <div className="space-y-3">
        {data?.notifications.map((n: any) => (
          <Card
            key={n.id}
            className={`p-4 flex items-start justify-between gap-4 ${
              n.is_read ? "opacity-75" : "border-l-4 border-l-[#D97998]"
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-[#FFF1F5] text-[#D97998] mt-0.5">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-bold text-sm text-[#28313B]">{n.title}</p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF1F5] text-[#C05D7E] uppercase font-semibold">
                    {n.category.replace("_", " ")}
                  </span>
                </div>
                <p className="text-xs text-[#687482] mt-1">{n.message}</p>
              </div>
            </div>
            {!n.is_read && (
              <button
                onClick={() => markRead(n.id)}
                className="text-xs font-semibold text-[#D97998] hover:underline shrink-0"
              >
                Mark read
              </button>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};
