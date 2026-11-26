import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../lib/api";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: "admin" | "teacher" | "outreach";
  role_display: string;
  assigned_school_id?: number | null;
  assigned_worker_id?: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem("shikshasetu_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const token = localStorage.getItem("shikshasetu_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/api/auth/me")
      .then((res) => {
        setUser(res.data);
        localStorage.setItem("shikshasetu_user", JSON.stringify(res.data));
      })
      .catch(() => {
        localStorage.removeItem("shikshasetu_token");
        localStorage.removeItem("shikshasetu_user");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post("/api/auth/login", { email, password });
    localStorage.setItem("shikshasetu_token", res.data.access_token);
    localStorage.setItem("shikshasetu_user", JSON.stringify(res.data.user));
    setUser(res.data.user);
  };

  const logout = async () => {
    try {
      await api.post("/api/auth/logout");
    } catch {
      // ignore
    }
    localStorage.removeItem("shikshasetu_token");
    localStorage.removeItem("shikshasetu_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
