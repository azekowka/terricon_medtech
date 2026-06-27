"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronsUpDown, MapPin, Search } from "lucide-react";

export interface CityOption {
  value: string;
  label: string;
  count?: number;
}

/** shadcn-style city combobox (custom popover, no extra deps). */
export function CitySelect({
  value,
  onChange,
  options,
  allLabel,
  className = "",
}: {
  value: string;
  onChange: (value: string) => void;
  options: CityOption[];
  allLabel?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const current = value ? options.find((o) => o.value === value) : null;
  const label = current ? current.label : allLabel || "—";
  const filtered = q
    ? options.filter((o) => o.label.toLowerCase().includes(q.trim().toLowerCase()))
    : options;

  function pick(v: string) {
    onChange(v);
    setOpen(false);
    setQ("");
  }

  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition hover:bg-slate-50 focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
      >
        <span className="flex min-w-0 items-center gap-2">
          <MapPin size={15} className="shrink-0 text-brand-500" />
          <span className="truncate">{label}</span>
        </span>
        <ChevronsUpDown size={15} className="shrink-0 text-slate-400" />
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-1.5 w-64 max-w-[80vw] overflow-hidden rounded-xl border border-slate-100 bg-white shadow-hover">
          {options.length > 8 && (
            <div className="relative border-b border-slate-100 p-2">
              <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={15} />
              <input
                autoFocus
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Поиск…"
                className="w-full rounded-lg border border-slate-200 bg-white py-1.5 pl-8 pr-2 text-sm outline-none focus:border-brand-400"
              />
            </div>
          )}
          <div className="max-h-64 overflow-y-auto p-1">
            {allLabel && (
              <Item active={!value} label={allLabel} onClick={() => pick("")} />
            )}
            {filtered.map((o) => (
              <Item
                key={o.value}
                active={value === o.value}
                label={o.label}
                count={o.count}
                onClick={() => pick(o.value)}
              />
            ))}
            {filtered.length === 0 && (
              <p className="px-3 py-4 text-center text-sm text-slate-400">—</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Item({
  active,
  label,
  count,
  onClick,
}: {
  active: boolean;
  label: string;
  count?: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition ${
        active ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      <Check size={15} className={`shrink-0 ${active ? "text-brand-600" : "text-transparent"}`} />
      <span className="truncate">{label}</span>
      {count != null && <span className="ml-auto shrink-0 text-xs text-slate-400">{count}</span>}
    </button>
  );
}
