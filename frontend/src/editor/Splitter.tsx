import { useEffect, useRef } from "react";

interface Props {
  /** Called while dragging with the horizontal distance (px) from where the drag started. */
  onDrag: (dx: number) => void;
  onDragStart: () => void;
  onDoubleClick?: () => void;
  label: string;
  hint?: string; // tooltip after the label
  className?: string;
}

/** A vertical drag handle between two columns. Double-click collapses (via onDoubleClick). */
export function Splitter({ onDrag, onDragStart, onDoubleClick, label, hint = "drag to resize, double-click to collapse", className = "" }: Props) {
  const startX = useRef<number | null>(null);
  // Dragging can collapse the column, unmounting this handle mid-drag: don't leave the cursor stuck.
  useEffect(() => () => document.body.classList.remove("resizing"), []);
  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      title={`${label}: ${hint}`}
      className={`splitter ${className}`}
      onDoubleClick={onDoubleClick}
      onPointerDown={(e) => {
        e.preventDefault();
        e.currentTarget.setPointerCapture(e.pointerId);
        startX.current = e.clientX;
        document.body.classList.add("resizing");
        onDragStart();
      }}
      onPointerMove={(e) => {
        if (startX.current !== null) onDrag(e.clientX - startX.current);
      }}
      onPointerUp={(e) => {
        e.currentTarget.releasePointerCapture(e.pointerId);
        startX.current = null;
        document.body.classList.remove("resizing");
      }}
    />
  );
}

export function readNumber(key: string, fallback: number): number {
  try {
    const value = Number(localStorage.getItem(key));
    return Number.isFinite(value) && value > 0 ? value : fallback;
  } catch {
    return fallback;
  }
}

export function store(key: string, value: string | number | boolean) {
  try {
    localStorage.setItem(key, String(value));
  } catch {
    /* ignore */
  }
}
