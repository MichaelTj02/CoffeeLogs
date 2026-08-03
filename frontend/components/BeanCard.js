import Link from "next/link";

import StarButton from "@/components/StarButton";
import { formatDate, formatPrice } from "@/lib/format";

export default function BeanCard({ bean, onToggleFavourite, onDelete, busy }) {
  const methodCount = bean.method_count ?? 0;
  const roastDate = formatDate(bean.roast_date);
  const price = formatPrice(bean.price);

  return (
    <article className={bean.is_favourite ? "card bean-card favourite" : "card bean-card"}>
      <div className="bean-card-head">
        <div>
          <Link href={`/beans/${bean.id}`} className="bean-name">
            {bean.name}
          </Link>
          <p className="bean-roaster">{bean.roaster}</p>
        </div>
        {onToggleFavourite && (
          <StarButton
            active={bean.is_favourite}
            busy={busy}
            onToggle={() => onToggleFavourite(bean)}
          />
        )}
      </div>

      <dl className="bean-meta">
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
      </dl>

      {bean.notes && <p className="bean-notes">{bean.notes}</p>}

      <div className="bean-card-foot">
        <span className="badge">
          {methodCount} {methodCount === 1 ? "method" : "methods"}
        </span>
        <div className="bean-card-actions">
          <Link href={`/beans/${bean.id}`} className="button subtle">
            Open
          </Link>
          {onDelete && (
            <button type="button" className="button danger" onClick={() => onDelete(bean)}>
              Delete
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
