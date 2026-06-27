"use client";

import { useEffect, useRef, useState } from "react";
import { Globe, Check, ChevronDown } from "lucide-react";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { LOCALES, Locale } from "@/lib/i18n/messages";

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const current = LOCALES.find((l) => l.code === locale) || LOCALES[0];

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 rounded-xl px-2.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
        aria-label="Language"
      >
        <Globe size={16} />
        <span className="hidden sm:inline">{current.short}</span>
        <ChevronDown size={14} className={`transition ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-1 w-40 overflow-hidden rounded-xl border border-slate-100 bg-white shadow-hover">
          {LOCALES.map((l) => (
            <button
              key={l.code}
              onClick={() => {
                setLocale(l.code as Locale);
                setOpen(false);
              }}
              className={`flex w-full items-center justify-between px-3 py-2.5 text-left text-sm transition ${
                l.code === locale ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-700 hover:bg-slate-50"
              }`}
            >
              {l.label}
              {l.code === locale && <Check size={15} className="text-brand-600" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
