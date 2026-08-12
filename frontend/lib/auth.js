import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { getMe, logout } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      try {
        setUser(await getMe());
      } catch {
        // Any failure means signed out — including the status-less error the fetch wrapper
        // throws when the backend is down, which would otherwise be a permanent spinner.
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  useEffect(() => {
    function handleUnauthorized() {
      setUser(null);
    }
    window.addEventListener("coffeelogs:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("coffeelogs:unauthorized", handleUnauthorized);
  }, []);

  // Login and register already return the user, and _app.js never remounts on client-side
  // navigation — without storing it here the guard would bounce straight back to /login.
  const signIn = useCallback((signedInUser) => {
    setUser(signedInUser);
  }, []);

  const signOut = useCallback(async () => {
    try {
      await logout();
    } catch {
      // A failed server call must not strand the browser in a signed-in state.
    }
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signOut }),
    [user, loading, signIn, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
