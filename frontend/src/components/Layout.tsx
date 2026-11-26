import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  CalendarClock,
  ClipboardCheck,
  FileSpreadsheet,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  School,
  ShieldAlert,
  TrendingUp,
  Users,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";

interface NavItem {
  to: string;
  label: string;
  icon: React.FC<{ className?: string }>;
  roles: Array<"admin" | "teacher" | "outreach">;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Foundation Dashboard", icon: LayoutDashboard, roles: ["admin", "teacher", "outreach"] },
  { to: "/schools", label: "School Analytics", icon: School, roles: ["admin", "teacher"] },
  { to: "/students", label: "Student Profiles", icon: Users, roles: ["admin", "teacher", "outreach"] },
  { to: "/risk-intelligence", label: "Risk Intelligence", icon: ShieldAlert, roles: ["admin", "teacher"] },
  { to: "/planner", label: "Intervention Planner", icon: CalendarClock, roles: ["admin", "teacher", "outreach"] },
  { to: "/interventions", label: "Intervention Lifecycle", icon: ClipboardCheck, roles: ["admin", "teacher", "outreach"] },
  { to: "/outcomes", label: "Outcome Analytics", icon: Activity, roles: ["admin", "teacher", "outreach"] },
  { to: "/assistant", label: "AI Teacher Assistant", icon: Bot, roles: ["admin", "teacher", "outreach"] },
  { to: "/impact-reports", label: "Impact Reports", icon: TrendingUp, roles: ["admin", "teacher"] },
  { to: "/data-upload", label: "Data Upload & CSV", icon: FileSpreadsheet, roles: ["admin"] },
  { to: "/notifications", label: "Notifications", icon: Bell, roles: ["admin", "teacher", "outreach"] },
];

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [draftCount, setDraftCount] = useState(0);

  useEffect(() => {
    const updateOnline = () => setIsOnline(navigator.onLine);
    const updateDraftCount = () => {
      try {
        const drafts = JSON.parse(localStorage.getItem("shikshasetu_offline_drafts") || "[]");
        setDraftCount(Array.isArray(drafts) ? drafts.length : 0);
      } catch {
        setDraftCount(0);
      }
    };
    window.addEventListener("online", updateOnline);
    window.addEventListener("offline", updateOnline);
    window.addEventListener("storage", updateDraftCount);
    updateDraftCount();

    api
      .get("/api/notifications")
      .then((res) => setUnreadCount(res.data.unread_count || 0))
      .catch(() => {});

    return () => {
      window.removeEventListener("online", updateOnline);
      window.removeEventListener("offline", updateOnline);
      window.removeEventListener("storage", updateDraftCount);
    };
  }, []);

  const visibleNav = NAV_ITEMS.filter((item) => user && item.roles.includes(user.role));

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-[#FFF9FB] text-[#28313B]">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/25 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-68 bg-white border-r border-[#F3DCE3] flex flex-col transition-transform duration-200 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="p-5 border-b border-[#F3DCE3] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FFF1F5] border border-[#F6C9D5] flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-[#D97998]" />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-tight text-[#28313B]">ShikshaSetu Foundation</h1>
              <p className="text-[11px] text-[#687482]">Intervention Intelligence</p>
            </div>
          </div>
          <button
            className="lg:hidden p-1.5 rounded-lg hover:bg-[#FFF1F5]"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar" aria-label="Primary navigation">
          {visibleNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[#FFF1F5] text-[#C05D7E] border border-[#F6C9D5]"
                      : "text-[#687482] hover:bg-[#FFF9FB] hover:text-[#28313B]"
                  }`
                }
              >
                <span className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </span>
                {item.to === "/notifications" && unreadCount > 0 && (
                  <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-[#D97998] text-white">
                    {unreadCount}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-[#F3DCE3] bg-[#FFF9FB]">
          <div className="bg-white border border-[#F3DCE3] rounded-xl p-3 mb-3">
            <p className="text-xs font-semibold text-[#28313B] truncate">{user?.full_name}</p>
            <p className="text-[11px] text-[#D97998] font-medium mt-0.5">{user?.role_display}</p>
            <p className="text-[11px] text-[#687482] truncate mt-0.5">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-[#687482] hover:text-[#C05D7E] hover:bg-[#FFF1F5] border border-[#F3DCE3] transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-20 bg-white/95 backdrop-blur border-b border-[#F3DCE3] px-4 lg:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden p-2 rounded-xl border border-[#F3DCE3] hover:bg-[#FFF1F5]"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-[#FFF1F5] text-[#C05D7E] border border-[#F6C9D5]">
                <BarChart3 className="w-3.5 h-3.5" />
                Veltris Challenge A • Demo Mode (Synthetic Student Records Labelled)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {draftCount > 0 && (
              <NavLink
                to="/interventions"
                className="text-xs font-medium px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200"
              >
                {draftCount} Offline Draft(s)
              </NavLink>
            )}
            <span
              className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${
                isOnline
                  ? "bg-[#E8F5EC] text-[#3B7F60] border-[#CBE7D4]"
                  : "bg-amber-50 text-amber-800 border-amber-200"
              }`}
              title="Connectivity status for field teams"
            >
              {isOnline ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              {isOnline ? "Online" : "Offline Mode"}
            </span>
            <NavLink
              to="/notifications"
              className="relative p-2 rounded-xl border border-[#F3DCE3] hover:bg-[#FFF1F5] transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4 text-[#687482]" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#D97998] text-white text-[10px] font-bold flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </NavLink>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
