import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

/* ── Types ── */
export interface AuthUser {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

interface AuthCtx {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  authFetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthCtx | null>(null);

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthCtx {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

/* ── Helper: authFetch factory ── */
function makeAuthFetch(
  getToken: () => string | null,
  onUnauthorized: () => void,
) {
  return async (input: RequestInfo, init?: RequestInit): Promise<Response> => {
    const token = getToken();
    const headers = new Headers(init?.headers);
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const res = await fetch(input, { ...init, headers });
    if (res.status === 401) {
      onUnauthorized();
    }
    return res;
  };
}

/* ── Storage keys ── */
const TOKEN_KEY = "agentbim_access_token";
const REFRESH_KEY = "agentbim_refresh_token";
const USER_KEY = "agentbim_user";

/* ── Provider ── */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const stored = localStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY),
  );
  const [loading, setLoading] = useState(true);

  // Persist to localStorage
  const saveAuth = useCallback((data: TokenResponse) => {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_KEY, data.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // Try refresh on mount if we have a refresh token
  useEffect(() => {
    const tryRefresh = async () => {
      const refreshToken = localStorage.getItem(REFRESH_KEY);
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (!refreshToken || !storedToken) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch("/api/auth/refresh", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (res.ok) {
          const data: TokenResponse = await res.json();
          saveAuth(data);
        } else {
          clearAuth();
        }
      } catch {
        // Keep existing token, will fail on next request
      } finally {
        setLoading(false);
      }
    };
    tryRefresh();
  }, [saveAuth, clearAuth]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || "Eroare la autentificare");
      }
      const data: TokenResponse = await res.json();
      saveAuth(data);
    },
    [saveAuth],
  );

  const register = useCallback(
    async (email: string, username: string, password: string) => {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || "Eroare la inregistrare");
      }
      const data: TokenResponse = await res.json();
      saveAuth(data);
    },
    [saveAuth],
  );

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  const authFetch = useCallback(
    makeAuthFetch(
      () => token,
      () => clearAuth(),
    ),
    [token, clearAuth],
  );

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, register, logout, authFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}
