import { useState } from "react";

import { blankToNull, numberOrNull } from "@/lib/format";

const EMPTY = {
  brewed_at: "",
  dose_grams: "",
  yield_grams: "",
  rating: "",
  notes: "",
};

// One instance per method section, so each keeps its own independent form state.
export default function AttemptForm({ onSubmit }) {
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError(null);

    // Blank brewed_at goes over as null and the API defaults it to now. Blank rating goes
    // over as null rather than "", which would 422.
    const payload = {
      brewed_at: blankToNull(form.brewed_at),
      dose_grams: numberOrNull(form.dose_grams),
      yield_grams: numberOrNull(form.yield_grams),
      rating: numberOrNull(form.rating),
      notes: blankToNull(form.notes),
    };

    try {
      await onSubmit(payload);
      setForm(EMPTY);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="subform" onSubmit={handleSubmit}>
      <h3>Log an attempt</h3>
      <div className="form-grid">
        <div className="field">
          <label>
            Dose (g) <span className="required">*</span>
          </label>
          <input
            type="number"
            step="0.1"
            min="0.1"
            value={form.dose_grams}
            onChange={(e) => update("dose_grams", e.target.value)}
            placeholder="18"
            required
          />
        </div>

        <div className="field">
          <label>
            Yield (g) <span className="required">*</span>
          </label>
          <input
            type="number"
            step="0.1"
            min="0.1"
            value={form.yield_grams}
            onChange={(e) => update("yield_grams", e.target.value)}
            placeholder="300"
            required
          />
        </div>

        <div className="field">
          <label>Brewed at</label>
          <input
            type="datetime-local"
            value={form.brewed_at}
            onChange={(e) => update("brewed_at", e.target.value)}
          />
        </div>

        <div className="field">
          <label>Rating</label>
          <select value={form.rating} onChange={(e) => update("rating", e.target.value)}>
            <option value="">No rating</option>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {"★".repeat(n)} ({n})
              </option>
            ))}
          </select>
        </div>

        <div className="field wide">
          <label>Notes</label>
          <textarea
            value={form.notes}
            onChange={(e) => update("notes", e.target.value)}
            placeholder="Ground a touch finer, 30s bloom. Sweeter than last time."
          />
        </div>
      </div>

      {error && <p className="field-error">{error}</p>}

      <div className="form-actions">
        <button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Add attempt"}
        </button>
      </div>
    </form>
  );
}
