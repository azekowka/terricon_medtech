import Link from "next/link";
import { api } from "@/lib/api";
import { SearchBar } from "@/components/SearchBar";
import { categoryMeta, formatDate, formatKzt } from "@/lib/format";
import type { Meta, ServiceItem } from "@/lib/types";
import { Building2, Clock, MapPin, TrendingDown } from "lucide-react";

export const dynamic = "force-dynamic";

async function getData(): Promise<{ meta: Meta | null; services: ServiceItem[] }> {
  try {
    const [meta, services] = await Promise.all([api.meta(), api.services()]);
    return { meta, services };
  } catch {
    return { meta: null, services: [] };
  }
}

export default async function HomePage() {
  const { meta, services } = await getData();
  const popular = [...services].sort((a, b) => b.offers_count - a.offers_count).slice(0, 12);
  const byCat: Record<string, ServiceItem[]> = {};
  for (const s of services) (byCat[s.category] ||= []).push(s);

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-600 via-brand-600 to-teal-600">
        <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(circle_at_20%_20%,white,transparent_40%),radial-gradient(circle_at_80%_0,white,transparent_30%)]" />
        <div className="container-page relative py-14 sm:py-20">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white">
            <TrendingDown size={14} /> Aviasales для медицины · Казахстан
          </p>
          <h1 className="max-w-3xl text-3xl font-extrabold leading-tight text-white sm:text-5xl">
            Сравните цены на анализы, приёмы врачей и диагностику
          </h1>
          <p className="mt-4 max-w-2xl text-base text-brand-50 sm:text-lg">
            Один поиск вместо десятков сайтов клиник. Актуальные прайсы из открытых
            источников — выбирайте выгодное предложение рядом с вами.
          </p>
          <div className="mt-7 max-w-2xl">
            <SearchBar size="lg" />
          </div>
          {meta && (
            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-brand-50">
              <Stat icon={<Building2 size={16} />} value={meta.counts.clinics} label="клиник" />
              <Stat icon={<TrendingDown size={16} />} value={meta.counts.active_prices} label="актуальных цен" />
              <Stat icon={<MapPin size={16} />} value={meta.counts.cities} label="городов" />
              <Stat icon={<Clock size={16} />} value={meta.counts.services} label="видов услуг" />
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
              <Link
                key={c.key}
                href={`/search?category=${c.key}`}
                className="card flex items-center gap-3 p-4 transition hover:shadow-hover"
              >
                <span className="text-2xl">{cm.emoji}</span>
                <span>
                  <span className="block font-semibold text-ink">{c.label}</span>
                  <span className="text-xs text-slate-400">
                    {(byCat[c.key] || []).length} услуг
                  </span>
                </span>
              </Link>
            );
          })}
        </section>

        {/* Popular services */}
        <section className="mt-12">
          <div className="mb-4 flex items-end justify-between">
            <h2 className="text-xl font-bold text-ink">Популярные услуги</h2>
            <span className="text-sm text-slate-400">
              {meta?.last_updated ? `Обновлено: ${formatDate(meta.last_updated)}` : ""}
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
                    <span className={`flex h-10 w-10 items-center justify-center rounded-xl text-lg ${cm.color}`}>
                      {cm.emoji}
                    </span>
                    <span>
                      <span className="block font-semibold leading-tight text-ink group-hover:text-brand-700">
                        {s.name}
                      </span>
                      <span className="text-xs text-slate-400">{cm.label}</span>
                    </span>
                  </span>
                  <span className="shrink-0 rounded-lg bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-500">
                    {s.offers_count} клиник
                  </span>
                </Link>
              );
            })}
          </div>
        </section>

        {/* How it works */}
        <section className="mt-14 grid gap-4 sm:grid-cols-3">
          {[
            ["1", "Ищите услугу", "Введите название анализа или приёма — поиск понимает синонимы и сокращения."],
            ["2", "Сравнивайте цены", "Видите все клиники с ценами, адресами и датой обновления прайса."],
            ["3", "Выбирайте выгодно", "Сортируйте по цене или расстоянию и переходите на сайт клиники."],
          ].map(([n, t, d]) => (
            <div key={n} className="card p-6">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 font-bold text-white">
                {n}
              </span>
              <h3 className="mt-3 font-bold text-ink">{t}</h3>
              <p className="mt-1 text-sm text-slate-500">{d}</p>
            </div>
          ))}
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
