import { createContext, useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import api, { setApiAuthToken } from "../api/axios";

const AuthContext = createContext(null);

const STORAGE_TOKEN = "vyana_auth_token";
const STORAGE_USER = "vyana_auth_user";

function readStoredUser() {
  try {
    const rawUser = localStorage.getItem(STORAGE_USER);
    return rawUser ? JSON.parse(rawUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_TOKEN) || "");
  const [user, setUser] = useState(() => readStoredUser());
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    setApiAuthToken(token);
  }, [token]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    let active = true;
    api
      .get("/auth/me")
      .then((response) => {
        if (!active) {
          return;
        }

        const nextUser = response.data?.data?.user || null;
        setUser(nextUser);
        if (nextUser) {
          localStorage.setItem(STORAGE_USER, JSON.stringify(nextUser));
        }
      })
      .catch(() => {
        logout({ silent: true });
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const login = async ({ role, accessCode, displayName }) => {
    const response = await api.post("/auth/login", {
      role,
      access_code: accessCode,
      display_name: displayName || undefined,
    });

    const nextToken = response.data?.data?.token || "";
    const nextUser = response.data?.data?.user || null;

    if (!nextToken || !nextUser) {
      throw new Error("Login did not return a valid session");
    }

    setToken(nextToken);
    setUser(nextUser);
    localStorage.setItem(STORAGE_TOKEN, nextToken);
    localStorage.setItem(STORAGE_USER, JSON.stringify(nextUser));
    toast.success(`Welcome ${nextUser.display_name}`);
    return nextUser;
  };

  const logout = async ({ silent = false } = {}) => {
    setToken("");
    setUser(null);
    localStorage.removeItem(STORAGE_TOKEN);
    localStorage.removeItem(STORAGE_USER);
    setApiAuthToken("");

    if (!silent) {
      try {
        await api.post("/auth/logout");
      } catch {
        // Client-side logout still succeeds even if the request fails.
      }
      toast.success("Signed out");
    }
  };

  return <AuthContext.Provider value={{ token, user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return value;
}