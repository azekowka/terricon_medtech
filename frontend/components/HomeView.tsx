"use client";

import Link from "next/link";
import { Building2, Check, Clock, GitCompareArrows, MapPin, RefreshCcw, ShieldCheck, TrendingDown } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";
import { categoryMeta, formatDate } from "@/lib/format";
import type { Meta, ServiceItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function HomeView({ meta, popular }: { meta: Meta | null; popular: ServiceItem[] }) {
  const { t } = useI18n();
  const byCatCount = meta?.services_by_category || {};

  return (
    <div>
      {/* Hero — clean single-hue brand band (no busy gradient / dot pattern) */}
      <section className="relative isolate overflow-hidden bg-brand-600">
        <div className="absolute inset-x-0 top-0 -z-10 h-px bg-white/10" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-white/[0.07] to-transparent" />
        <div className="container-page py-14 sm:py-[4.75rem]">
          <p className="mb-5 inline-flex items-center gap-1.5 rounded-full bg-white/12 px-3 py-1 text-[13px] font-medium text-white/95 ring-1 ring-inset ring-white/15">
            <TrendingDown size={14} /> {t("home.badge")}
          </p>
          <h1 className="max-w-3xl text-[2rem] font-bold leading-[1.08] tracking-tighter text-white sm:text-[3.25rem]">
            {t("home.title")}
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-white/80 sm:text-lg">{t("home.subtitle")}</p>
          <div className="mt-8 max-w-2xl">
            <SearchBar size="lg" />
            <p className="mt-3 flex items-center gap-1.5 text-[13px] text-white/70">
              <Check size={14} className="shrink-0 text-white/80" /> {t("home.trust")}
            </p>
          </div>
          {meta && (
            <div className="mt-7 flex flex-wrap gap-2.5">
              <StatPill icon={<Building2 size={15} />} value={meta.counts.clinics} label={t("home.stat.clinics")} />
              <StatPill icon={<TrendingDown size={15} />} value={meta.counts.active_prices} label={t("home.stat.prices")} />
              <StatPill icon={<MapPin size={15} />} value={meta.counts.cities} label={t("home.stat.cities")} />
              <StatPill icon={<Clock size={15} />} value={meta.counts.services} label={t("home.stat.services")} />
            </div>
          )}
        </div>
      </section>

      <div className="container-page">
        {/* Category quick filters */}
        <section className="relative -mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {meta?.categories.map((c) => {
            const cm = categoryMeta(c.key);
            const Icon = cm.icon;
            return (
              <Link
                key={c.key}
                href={`/search?category=${c.key}`}
                className="card flex items-center gap-3 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-hover"
              >
                <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${cm.color}`}>
                  <Icon size={20} strokeWidth={1.75} />
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-ink">{c.label}</span>
                  <span className="text-xs text-slate-400">{byCatCount[c.key] || 0} {t("home.services")}</span>
                </span>
              </Link>
            );
          })}
        </section>

        {/* Popular services */}
        <section className="mt-12">
          <div className="mb-4 flex items-end justify-between">
            <h2 className="text-xl font-bold tracking-tight text-ink">{t("home.popular")}</h2>
            <span className="text-sm text-slate-400">
              {meta?.last_updated ? `${t("search.updated")}: ${formatDate(meta.last_updated)}` : ""}
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {popular.map((s) => {
              const cm = categoryMeta(s.category);
              const Icon = cm.icon;
              return (
                <Link
                  key={s.id}
                  href={`/search?service_id=${s.id}&name=${encodeURIComponent(s.name)}`}
                  className="card group flex items-center justify-between gap-3 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-hover"
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${cm.color}`}>
                      <Icon size={18} strokeWidth={1.75} />
                    </span>
                    <span className="min-w-0">
                      <span className="block truncate font-semibold leading-tight text-ink group-hover:text-brand-700">{s.name}</span>
                      <span className="text-xs text-slate-400">{cm.label}</span>
                    </span>
                  </span>
                  <span className="shrink-0 rounded-lg bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-500">
                    {s.offers_count} {t("home.clinicsCount")}
                  </span>
                </Link>
              );
            })}
          </div>
        </section>

        {/* Value props */}
        <section className="mt-14 mb-2">
          <h2 className="mb-4 text-xl font-bold tracking-tight text-ink">{t("home.feat.title")}</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <Feature icon={<GitCompareArrows size={20} strokeWidth={1.75} />} title={t("home.feat.compare.t")} desc={t("home.feat.compare.d")} />
            <Feature icon={<ShieldCheck size={20} strokeWidth={1.75} />} title={t("home.feat.open.t")} desc={t("home.feat.open.d")} />
            <Feature icon={<RefreshCcw size={20} strokeWidth={1.75} />} title={t("home.feat.fresh.t")} desc={t("home.feat.fresh.d")} />
          </div>
        </section>
      </div>
    </div>
  );
}

function Feature({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="card p-5">
      <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">{icon}</span>
      <h3 className="mt-3.5 font-bold text-ink">{title}</h3>
      <p className="mt-1 text-sm leading-relaxed text-slate-500">{desc}</p>
    </div>
  );
}

function StatPill({ icon, value, label }: { icon: React.ReactNode; value: number; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-white/12 px-3.5 py-1.5 text-sm text-white/80 ring-1 ring-inset ring-white/15">
      <span className="text-white/70">{icon}</span>
      <b className="font-semibold text-white">{new Intl.NumberFormat("ru-RU").format(value)}</b>
      {label}
    </span>
  );
}
