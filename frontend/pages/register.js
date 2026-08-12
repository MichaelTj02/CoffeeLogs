import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";

import { register } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Register() {
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
      const user = await register(email.trim(), password);
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
        <h1>Create an account</h1>
        <p>One account per coffee drinker. Registering signs you straight in.</p>
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
            {/* No minLength: the server owns the 8-character rule, and a native tooltip
                would hide its 422 from the notice above. */}
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              maxLength={128}
              required
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? "Creating…" : "Create account"}
          </button>
        </div>
      </form>

      <p className="auth-alt">
        Already have an account? <Link href="/login">Sign in</Link>
      </p>
    </div>
  );
}
