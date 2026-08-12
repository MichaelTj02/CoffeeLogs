import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import AttemptForm from "@/components/AttemptForm";
import StarButton from "@/components/StarButton";
import {
  createAttempt,
  createMethod,
  deleteAttempt,
  deleteBean,
  deleteMethod,
  getBean,
  setFavourite,
} from "@/lib/api";
import { brewRatio, formatDate, formatPrice, stars } from "@/lib/format";

export default function BeanDetail() {
  const router = useRouter();
  const { id } = router.query;

  const [bean, setBean] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [methodName, setMethodName] = useState("");
  const [methodError, setMethodError] = useState(null);
  const [addingMethod, setAddingMethod] = useState(false);

  const load = useCallback(async (beanId) => {
    try {
      setLoading(true);
      setError(null);
      setBean(await getBean(beanId));
    } catch (err) {
      setError(err.message);
      setBean(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // router.query is empty on first render, so an unguarded fetch would hit /beans/undefined.
  useEffect(() => {
    if (!router.isReady) return;
    load(id);
  }, [router.isReady, id, load]);

  // The one mutation here that skips the re-load: the star flips optimistically and
  // rolls back on failure, so a round trip would buy nothing.
  async function handleToggleFavourite() {
    const next = !bean.is_favourite;
    setBean((prev) => ({ ...prev, is_favourite: next }));
    try {
      await setFavourite(bean.id, next);
    } catch (err) {
      setBean((prev) => ({ ...prev, is_favourite: !next }));
      setError(err.message);
    }
  }

  async function handleAddMethod(event) {
    event.preventDefault();
    setAddingMethod(true);
    setMethodError(null);
    try {
      await createMethod(bean.id, methodName.trim());
      setMethodName("");
      await load(bean.id);
    } catch (err) {
      setMethodError(err.message);
    } finally {
      setAddingMethod(false);
    }
  }

  async function handleDeleteMethod(method) {
    const count = method.attempts.length;
    const confirmed = window.confirm(
      count === 0
        ? `Delete the "${method.name}" method?`
        : `Delete "${method.name}"? Its ${count} ${count === 1 ? "attempt" : "attempts"} go too.`
    );
    if (!confirmed) return;

    try {
      await deleteMethod(method.id);
      await load(bean.id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAddAttempt(methodId, payload) {
    await createAttempt(methodId, payload);
    await load(bean.id);
  }

  async function handleDeleteAttempt(attempt) {
    if (!window.confirm("Delete this attempt?")) return;
    try {
      await deleteAttempt(attempt.id);
      await load(bean.id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteBean() {
    const confirmed = window.confirm(
      `Delete "${bean.name}"? Its brew methods and every attempt under them go too.`
    );
    if (!confirmed) return;

    try {
      await deleteBean(bean.id);
      router.push("/logs");
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) {
    return <div className="state">Loading…</div>;
  }

  if (error && !bean) {
    return (
      <>
        <Link href="/logs" className="back-link">
          ← Back to logs
        </Link>
        <div className="notice error">{error}</div>
      </>
    );
  }

  if (!bean) return null;

  const roastDate = formatDate(bean.roast_date);
  const price = formatPrice(bean.price);

  return (
    <>
      <Link href="/logs" className="back-link">
        ← Back to logs
      </Link>

      {error && <div className="notice error">{error}</div>}

      <div className="card">
        <div className="detail-head">
          <div>
            <h1>{bean.name}</h1>
            <p className="bean-roaster">{bean.roaster}</p>
          </div>
          <div className="detail-actions">
            <StarButton active={bean.is_favourite} onToggle={handleToggleFavourite} />
            <button type="button" className="button danger" onClick={handleDeleteBean}>
              Delete bean
            </button>
          </div>
        </div>

        <dl className="bean-meta" style={{ marginTop: "1rem" }}>
          {bean.origin && (
            <div>
              <dt>Origin</dt>
              <dd>{bean.origin}</dd>
            </div>
          )}
          {roastDate && (
            <div>
              <dt>Roasted</dt>
              <dd>{roastDate}</dd>
            </div>
          )}
          {price && (
            <div>
              <dt>Price</dt>
              <dd>{price}</dd>
            </div>
          )}
          <div>
            <dt>Added</dt>
            <dd>{formatDate(bean.created_at)}</dd>
          </div>
        </dl>

        {bean.notes && <p className="bean-notes" style={{ marginTop: "1rem" }}>{bean.notes}</p>}
      </div>

      <section className="section">
        <div className="section-head">
          <h2>Brew methods</h2>
        </div>

        <form className="card" onSubmit={handleAddMethod}>
          <div className="inline-form">
            <div className="field">
              <label htmlFor="method-name">Add a method</label>
              <input
                id="method-name"
                value={methodName}
                onChange={(e) => {
                  setMethodName(e.target.value);
                  setMethodError(null);
                }}
                placeholder="V60, AeroPress, Espresso…"
                maxLength={50}
                required
              />
            </div>
            <button type="submit" disabled={addingMethod || methodName.trim() === ""}>
              {addingMethod ? "Adding…" : "Add method"}
            </button>
          </div>
          {methodError && <p className="field-error">{methodError}</p>}
        </form>

        {bean.brew_methods.length === 0 ? (
          <div className="state" style={{ marginTop: "1rem" }}>
            <strong>No brew methods yet</strong>
            Add one above, then log your attempts under it.
          </div>
        ) : (
          bean.brew_methods.map((method) => (
            <section className="method-section" key={method.id}>
              <header className="method-head">
                <span className="method-name">{method.name}</span>
                <div className="detail-actions">
                  <span className="badge">
                    {method.attempts.length}{" "}
                    {method.attempts.length === 1 ? "attempt" : "attempts"}
                  </span>
                  <button
                    type="button"
                    className="button danger"
                    onClick={() => handleDeleteMethod(method)}
                  >
                    Remove
                  </button>
                </div>
              </header>

              <div className="method-body">
                {method.attempts.length === 0 ? (
                  <p className="attempt-when">
                    Nothing brewed with this method yet — log your first attempt below.
                  </p>
                ) : (
                  <ul className="attempt-list">
                    {method.attempts.map((attempt) => (
                      <li className="attempt-row" key={attempt.id}>
                        <div>
                          <div className="attempt-main">
                            <span className="attempt-recipe">
                              {attempt.dose_grams}g → {attempt.yield_grams}g
                            </span>
                            <span className="attempt-ratio">
                              {brewRatio(attempt.dose_grams, attempt.yield_grams)}
                            </span>
                            {attempt.rating && (
                              <span className="attempt-rating">{stars(attempt.rating)}</span>
                            )}
                            <span className="attempt-when">{formatDate(attempt.brewed_at)}</span>
                          </div>
                          {attempt.notes && <p className="attempt-notes">{attempt.notes}</p>}
                        </div>
                        <button
                          type="button"
                          className="button danger"
                          onClick={() => handleDeleteAttempt(attempt)}
                        >
                          Delete
                        </button>
                      </li>
                    ))}
                  </ul>
                )}

                <AttemptForm
                  onSubmit={(payload) => handleAddAttempt(method.id, payload)}
                />
              </div>
            </section>
          ))
        )}
      </section>
    </>
  );
}
