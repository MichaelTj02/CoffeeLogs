import Link from "next/link";
import { useRouter } from "next/router";

import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { pathname } = useRouter();
  const { user, signOut } = useAuth();
  const logsActive = pathname === "/logs" || pathname.startsWith("/beans");

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="wordmark">
          Coffee<span>Logs</span>
        </Link>
        {user && (
          <nav className="nav-links">
            <Link href="/" className={pathname === "/" ? "nav-link active" : "nav-link"}>
              Add bean
            </Link>
            <Link href="/logs" className={logsActive ? "nav-link active" : "nav-link"}>
              Logs
            </Link>
            <span className="nav-user">{user.email}</span>
            {/* Signing out alone is enough: AuthGuard owns the redirect, and a push here
                would race its replace and leave the page behind Back. */}
            <button type="button" className="nav-logout" onClick={signOut}>
              Log out
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
