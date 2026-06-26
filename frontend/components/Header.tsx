"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, GitCompareArrows, Map, Settings } from "lucide-react";

const NAV = [
  { href: "/", label: "Поиск", icon: Activity },
  { href: "/compare", label: "Сравнение", icon: GitCompareArrows },
  { href: "/map", label: "Карта", icon: Map },
  { href: "/admin", label: "Админ", icon: Settings },
];

export function Header() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Activity size={20} />
          </span>
          <span className="text-lg font-extrabold tracking-tight text-ink">
            MedService<span className="text-brand-600">Price</span>
            <span className="text-slate-400">.kz</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" || pathname.startsWith("/search") : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium transition ${
                  active ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Icon size={16} />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
