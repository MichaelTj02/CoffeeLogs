import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";

import { login } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Login() {
  const router = useRouter();
  const { signIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // The email is trimmed, the password never is — whitespace can be part of it.
      const user = await login(email.trim(), password);
      signIn(user);
      router.replace("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="page-head">
        <h1>Sign in</h1>
        <p>Your beans, methods and attempts are yours alone.</p>
      </div>

      {error && <div className="notice error">{error}</div>}

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="field wide">
            <label htmlFor="email">
              Email <span className="required">*</span>
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              maxLength={255}
              required
            />
          </div>

          <div className="field wide">
            <label htmlFor="password">
              Password <span className="required">*</span>
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              maxLength={128}
              required
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </div>
      </form>

      <p className="auth-alt">
        No account yet? <Link href="/register">Create one</Link>
      </p>
    </div>
  );
}
