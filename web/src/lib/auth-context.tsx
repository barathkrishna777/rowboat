"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { auth as authApi, User } from "./api";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("auth_token");
    if (stored) {
      setToken(stored);
      authApi.me().then(setUser).catch(() => {
        localStorage.removeItem("auth_token");
      }).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    localStorage.setItem("auth_token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const register = async (name: string, email: string, password: string) => {
    const res = await authApi.register(name, email, password);
    localStorage.setItem("auth_token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
