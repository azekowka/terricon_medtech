"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Suggestion } from "@/lib/types";
import { categoryMeta } from "@/lib/format";

export function SearchBar({
  size = "lg",
  initialValue = "",
}: {
  size?: "lg" | "md";
  initialValue?: string;
}) {
  const router = useRouter();
  const [value, setValue] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(-1);
  const boxRef = useRef<HTMLDivElement>(null);
  const debounce = useRef<ReturnType<typeof setTimeout>>();
  const userTyped = useRef(false);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Keep the input in sync when the active search target changes via in-place
  // navigation (same route, only query params change -> no remount).
  useEffect(() => {
    setValue(initialValue);
    userTyped.current = false;
    setOpen(false);
  }, [initialValue]);

  useEffect(() => {
    if (debounce.current) clearTimeout(debounce.current);
    // Don't fire (or auto-open) for the initial programmatic value — only when
    // the user actually types.
    if (!userTyped.current || value.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    setLoading(true);
    debounce.current = setTimeout(async () => {
      try {
        const res = await api.autocomplete(value.trim());
        setSuggestions(res.suggestions);
        setOpen(true);
        setActive(-1);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 180);
  }, [value]);

  function goService(s: Suggestion) {
    router.push(`/search?service_id=${s.id}&name=${encodeURIComponent(s.name)}`);
    setOpen(false);
  }

  function submitFree() {
    if (!value.trim()) return;
    router.push(`/search?q=${encodeURIComponent(value.trim())}`);
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (active >= 0 && suggestions[active]) goService(suggestions[active]);
      else submitFree();
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  const pad = size === "lg" ? "py-4 text-base" : "py-2.5 text-sm";

  return (
    <div ref={boxRef} className="relative w-full">
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
          size={size === "lg" ? 22 : 18}
        />
        <input
          value={value}
          onChange={(e) => {
            userTyped.current = true;
            setValue(e.target.value);
          }}
          onFocus={() => suggestions.length && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Например: общий анализ крови, УЗИ, приём терапевта…"
          className={`w-full rounded-2xl border border-slate-200 bg-white pl-12 pr-28 ${pad} font-medium shadow-card outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100`}
        />
        <button onClick={submitFree} className="btn-primary absolute right-2 top-1/2 -translate-y-1/2">
          {loading ? <Loader2 className="animate-spin" size={16} /> : "Найти"}
        </button>
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute z-40 mt-2 w-full overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-hover">
          {suggestions.map((s, i) => {
            const cm = categoryMeta(s.category);
            return (
              <button
                key={s.id}
                onMouseEnter={() => setActive(i)}
                onClick={() => goService(s)}
                className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition ${
                  active === i ? "bg-brand-50" : "hover:bg-slate-50"
                }`}
              >
                <span className="flex items-center gap-3">
                  <span className="text-lg">{cm.emoji}</span>
                  <span>
                    <span className="block font-semibold text-ink">{s.name}</span>
                    <span className="mt-0.5 flex items-center gap-1.5">
                      <span className={`chip ${cm.color}`}>{cm.label}</span>
                      {s.specialty && <span className="text-xs text-slate-400">{s.specialty}</span>}
                    </span>
                  </span>
                </span>
                <span className="shrink-0 text-xs font-medium text-slate-400">
                  {s.offers_count} клиник
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
