"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, GitCompareArrows, HeartPulse, Map, Settings, Stethoscope } from "lucide-react";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

const NAV = [
  { href: "/", key: "nav.search", icon: Activity },
  { href: "/compare", key: "nav.compare", icon: GitCompareArrows },
  { href: "/map", key: "nav.map", icon: Map },
  { href: "/doctors", key: "nav.doctors", icon: Stethoscope },
  { href: "/lechenie", key: "nav.lechenie", icon: HeartPulse },
  { href: "/admin", key: "nav.admin", icon: Settings },
];

export function Header() {
  const pathname = usePathname();
  const { t } = useI18n();
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="text-[1.0625rem] font-bold tracking-tight text-ink">
            MedService<span className="text-brand-600">Price</span>.kz
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV.map(({ href, key, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" || pathname.startsWith("/search") : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-sm font-medium transition ${
                  active ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Icon size={16} />
                <span className="hidden md:inline">{t(key)}</span>
              </Link>
            );
          })}
          <span className="mx-1 h-5 w-px bg-slate-200" />
          <LanguageSwitcher />
        </nav>
      </div>
    </header>
  );
}
