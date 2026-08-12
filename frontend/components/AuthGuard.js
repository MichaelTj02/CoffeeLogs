import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

const PUBLIC_PATHS = ["/login", "/register"];

export default function AuthGuard({ children }) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const isPublic = PUBLIC_PATHS.includes(router.pathname);

  useEffect(() => {
    if (loading) return;
    if (!user && !isPublic) router.replace("/login");
    if (user && isPublic) router.replace("/");
  }, [loading, user, isPublic, router]);

  // router.replace is async, so every non-final state has to render something inert:
  // falling through would mount the real page for a frame and fire its fetches into 401s,
  // and flash the login form at an already signed-in user.
  if (loading || (!isPublic && !user) || (isPublic && user)) {
    return <div className="state">Loading…</div>;
  }

  return <>{children}</>;
}
