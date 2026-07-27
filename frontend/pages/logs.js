import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import BeanCard from "@/components/BeanCard";
import { deleteBean, getBeans, setFavourite } from "@/lib/api";

export default function Logs() {
  const [beans, setBeans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setBeans(await getBeans());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Optimistic: flip the star immediately, then reconcile. A toggle that waits for a
  // round-trip before painting reads as broken. Re-sorting is deferred to the reload so
  // the card does not jump out from under the cursor mid-click.
  async function handleToggleFavourite(bean) {
    const next = !bean.is_favourite;
    setBusyId(bean.id);
    setError(null);
    setBeans((prev) =>
      prev.map((b) => (b.id === bean.id ? { ...b, is_favourite: next } : b))
    );

    try {
      await setFavourite(bean.id, next);
      await load();
    } catch (err) {
      setBeans((prev) =>
        prev.map((b) => (b.id === bean.id ? { ...b, is_favourite: bean.is_favourite } : b))
      );
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(bean) {
    const confirmed = window.confirm(
      `Delete "${bean.name}"? Its brew methods and every attempt under them go too.`
    );
    if (!confirmed) return;

    setBusyId(bean.id);
    setError(null);
    try {
      await deleteBean(bean.id);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>Logs</h1>
        <p>Every bean you have logged. Favourites come first.</p>
      </div>

      {error && <div className="notice error">{error}</div>}

      {loading ? (
        <div className="state">Loading…</div>
      ) : beans.length === 0 ? (
        <div className="state">
          <strong>Nothing logged yet</strong>
          <Link href="/">Add your first bean →</Link>
        </div>
      ) : (
        <div className="bean-grid">
          {beans.map((bean) => (
            <BeanCard
              key={bean.id}
              bean={bean}
              busy={busyId === bean.id}
              onToggleFavourite={handleToggleFavourite}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </>
  );
}
