export default function StarButton({ active, onToggle, busy }) {
  return (
    <button
      type="button"
      className={active ? "star active" : "star"}
      onClick={onToggle}
      disabled={busy}
      aria-pressed={active}
      aria-label={active ? "Remove from favourites" : "Add to favourites"}
      title={active ? "Remove from favourites" : "Add to favourites"}
    >
      {active ? "★" : "☆"}
    </button>
  );
}
