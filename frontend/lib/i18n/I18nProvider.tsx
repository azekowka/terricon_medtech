"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { Locale, messages } from "./messages";

interface I18nCtx {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const Ctx = createContext<I18nCtx | null>(null);

function detect(): Locale {
  if (typeof navigator === "undefined") return "ru";
  const l = (navigator.language || "ru").toLowerCase();
  if (l.startsWith("kk") || l.startsWith("kz")) return "kk";
  if (l.startsWith("en")) return "en";
  return "ru";
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("ru");

  // restore saved or auto-detect on mount (client only)
  useEffect(() => {
    const saved = localStorage.getItem("locale") as Locale | null;
    const next = saved && messages[saved] ? saved : detect();
    setLocaleState(next);
    document.documentElement.lang = next;
  }, []);

  function setLocale(l: Locale) {
    setLocaleState(l);
    try {
      localStorage.setItem("locale", l);
      document.documentElement.lang = l;
    } catch {}
  }

  const t = useMemo(() => {
    const dict = messages[locale] || messages.ru;
    return (key: string, vars?: Record<string, string | number>) => {
      let s = dict[key] ?? messages.ru[key] ?? key;
      if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
      return s;
    };
  }, [locale]);

  return <Ctx.Provider value={{ locale, setLocale, t }}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nCtx {
  const c = useContext(Ctx);
  if (!c) return { locale: "ru", setLocale: () => {}, t: (k) => messages.ru[k] ?? k };
  return c;
}
