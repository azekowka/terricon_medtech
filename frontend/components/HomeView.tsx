"use client";

import Link from "next/link";
import { Building2, Clock, MapPin, TrendingDown } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";
import { categoryMeta, formatDate } from "@/lib/format";
import type { Meta, ServiceItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function HomeView({ meta, popular }: { meta: Meta | null; popular: ServiceItem[] }) {
  const { t } = useI18n();
  const byCatCount = meta?.services_by_category || {};

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-600 via-brand-600 to-teal-600">
        <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(circle_at_20%_20%,white,transparent_40%),radial-gradient(circle_at_80%_0,white,transparent_30%)]" />
        <div className="container-page relative py-14 sm:py-20">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white">
            <TrendingDown size={14} /> {t("home.badge")}
          </p>
          <h1 className="max-w-3xl text-3xl font-extrabold leading-tight text-white sm:text-5xl">
            {t("home.title")}
          </h1>
          <p className="mt-4 max-w-2xl text-base text-brand-50 sm:text-lg">{t("home.subtitle")}</p>
          <div className="mt-7 max-w-2xl">
            <SearchBar size="lg" />
          </div>
          {meta && (
            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-brand-50">
              <Stat icon={<Building2 size={16} />} value={meta.counts.clinics} label={t("home.stat.clinics")} />
              <Stat icon={<TrendingDown size={16} />} value={meta.counts.active_prices} label={t("home.stat.prices")} />
              <Stat icon={<MapPin size={16} />} value={meta.counts.cities} label={t("home.stat.cities")} />
              <Stat icon={<Clock size={16} />} value={meta.counts.services} label={t("home.stat.services")} />
            </div>
          )}
        </div>
      </section>

      <div className="container-page">
        {/* Category quick filters */}
        <section className="-mt-7 relative grid grid-cols-2 gap-3 sm:grid-cols-4">
          {meta?.categories.map((c) => {
            const cm = categoryMeta(c.key);
            return (
              <Link key={c.key} href={`/search?category=${c.key}`} className="card flex items-center gap-3 p-4 transition hover:shadow-hover">
                <span className="text-2xl">{cm.emoji}</span>
                <span>
                  <span className="block font-semibold text-ink">{c.label}</span>
                  <span className="text-xs text-slate-400">{byCatCount[c.key] || 0} {t("home.services")}</span>
                </span>
              </Link>
            );
          })}
        </section>

        {/* Popular services */}
        <section className="mt-12">
          <div className="mb-4 flex items-end justify-between">
            <h2 className="text-xl font-bold text-ink">{t("home.popular")}</h2>
            <span className="text-sm text-slate-400">
              {meta?.last_updated ? `${t("search.updated")}: ${formatDate(meta.last_updated)}` : ""}
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {popular.map((s) => {
              const cm = categoryMeta(s.category);
              return (
                <Link
                  key={s.id}
                  href={`/search?service_id=${s.id}&name=${encodeURIComponent(s.name)}`}
                  className="card group flex items-center justify-between gap-3 p-4 transition hover:-translate-y-0.5 hover:shadow-hover"
                >
                  <span className="flex items-center gap-3">
                    <span className={`flex h-10 w-10 items-center justify-center rounded-xl text-lg ${cm.color}`}>{cm.emoji}</span>
                    <span>
                      <span className="block font-semibold leading-tight text-ink group-hover:text-brand-700">{s.name}</span>
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
      </div>
    </div>
  );
}

function Stat({ icon, value, label }: { icon: React.ReactNode; value: number; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      {icon}
      <b className="font-bold text-white">{value}</b> {label}
    </span>
  );
}
