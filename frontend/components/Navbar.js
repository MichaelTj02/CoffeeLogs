import Link from "next/link";
import { useRouter } from "next/router";

export default function Navbar() {
  const { pathname } = useRouter();
  const logsActive = pathname === "/logs" || pathname.startsWith("/beans");

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="wordmark">
          Coffee<span>Logs</span>
        </Link>
        <nav className="nav-links">
          <Link href="/" className={pathname === "/" ? "nav-link active" : "nav-link"}>
            Add bean
          </Link>
          <Link href="/logs" className={logsActive ? "nav-link active" : "nav-link"}>
            Logs
          </Link>
        </nav>
      </div>
    </header>
  );
}
