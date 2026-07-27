import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import BeanCard from "@/components/BeanCard";
import { createBean, getBeans } from "@/lib/api";
import { blankToNull, numberOrNull } from "@/lib/format";

const EMPTY_FORM = {
  name: "",
  roaster: "",
  origin: "",
  roast_date: "",
  price: "",
  notes: "",
};

const RECENT_LIMIT = 5;

export default function Home() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setRecent(await getBeans(RECENT_LIMIT));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(null);

    // Optional fields must go over as null, not "". An empty date or number input yields
    // "", which the API rejects with a 422.
    const payload = {
      name: blankToNull(form.name),
      roaster: blankToNull(form.roaster),
      origin: blankToNull(form.origin),
      roast_date: blankToNull(form.roast_date),
      price: numberOrNull(form.price),
      notes: blankToNull(form.notes),
    };

    try {
      const bean = await createBean(payload);
      setForm(EMPTY_FORM);
      setSaved(bean);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>Add a bean</h1>
        <p>
          Log what you bought. Brew methods and attempts come later, from the bean&apos;s own
          page.
        </p>
      </div>

      {error && <div className="notice error">{error}</div>}
      {saved && (
        <div className="notice success">
          Saved <strong>{saved.name}</strong>.{" "}
          <Link href={`/beans/${saved.id}`}>Add a brew method →</Link>
        </div>
      )}

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="name">
              Name <span className="required">*</span>
            </label>
            <input
              id="name"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="Ethiopia Yirgacheffe"
              maxLength={120}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="roaster">
              Roaster <span className="required">*</span>
            </label>
            <input
              id="roaster"
              value={form.roaster}
              onChange={(e) => update("roaster", e.target.value)}
              placeholder="Local Roasters"
              maxLength={120}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="origin">Origin</label>
            <input
              id="origin"
              value={form.origin}
              onChange={(e) => update("origin", e.target.value)}
              placeholder="Ethiopia"
              maxLength={120}
            />
          </div>

          <div className="field">
            <label htmlFor="roast_date">Roast date</label>
            <input
              id="roast_date"
              type="date"
              value={form.roast_date}
              onChange={(e) => update("roast_date", e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="price">Price</label>
            <input
              id="price"
              type="number"
              step="0.01"
              min="0"
              max="9999.99"
              value={form.price}
              onChange={(e) => update("price", e.target.value)}
              placeholder="18.50"
            />
          </div>

          <div className="field wide">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              value={form.notes}
              onChange={(e) => update("notes", e.target.value)}
              placeholder="Floral, citrus, tea-like body."
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Add bean"}
          </button>
        </div>
      </form>

      <section className="section">
        <div className="section-head">
          <h2>Recently added</h2>
          <Link href="/logs" className="nav-inline">
            View all logs →
          </Link>
        </div>

        {loading ? (
          <div className="state">Loading…</div>
        ) : recent.length === 0 ? (
          <div className="state">
            <strong>No beans yet</strong>
            Add your first one above.
          </div>
        ) : (
          <div className="bean-grid">
            {recent.map((bean) => (
              <BeanCard key={bean.id} bean={bean} />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
