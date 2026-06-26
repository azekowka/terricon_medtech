"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CalendarCheck, ExternalLink, Star } from "lucide-react";
import { api } from "@/lib/api";
import type { HistorySeries, SearchResult, ServiceItem } from "@/lib/types";
import { SearchBar } from "@/components/SearchBar";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { formatKzt, relativeDays, categoryMeta } from "@/lib/format";

function CompareContent() {
  const params = useSearchParams();
  const serviceId = params.get("service_id") || "";
  const clinicIds = params.get("clinic_ids") || "";

  const [result, setResult] = useState<SearchResult | null>(null);
  const [history, setHistory] = useState<HistorySeries | null>(null);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.services({ sort: "popular", limit: 12 }).then(setServices).catch(() => {});
  }, []);

  useEffect(() => {
    if (!serviceId) return;
    setLoading(true);
    Promise.all([
      api.compare({ service_id: serviceId, clinic_ids: clinicIds || undefined }),
      api.history({ service_id: serviceId }),
    ])
      .then(([r, h]) => {
        setResult(r);
        setHistory(h);
      })
      .finally(() => setLoading(false));
  }, [serviceId, clinicIds]);

  if (!serviceId) {
    return (
      <div className="container-page pt-8">
        <h1 className="text-2xl font-extrabold text-ink">Сравнение цен</h1>
        <p className="mt-2 text-slate-500">Выберите услугу, чтобы сравнить предложения клиник.</p>
        <div className="mt-5 max-w-2xl">
          <SearchBar size="md" />
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {services.slice(0, 9).map((s) => {
            const cm = categoryMeta(s.category);
            return (
              <Link key={s.id} href={`/compare?service_id=${s.id}`} className="card flex items-center gap-3 p-4 hover:shadow-hover">
                <span className="text-xl">{cm.emoji}</span>
                <span className="font-semibold text-ink">{s.name}</span>
              </Link>
            );
          })}
        </div>
      </div>
    );
  }

  const offers = result?.offers || [];

  return (
    <div className="container-page pt-6">
      <div className="mb-5 max-w-2xl">
        <SearchBar size="md" initialValue={result?.service?.name || ""} />
      </div>

      <h1 className="text-2xl font-extrabold text-ink">
        Сравнение: {result?.service?.name || "услуга"}
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        {loading ? "Загрузка…" : `${offers.length} клиник · разница цен до ${formatKzt(
          (result?.stats?.max_price || 0) - (result?.stats?.min_price || 0),
        )}`}
      </p>

      {/* Comparison table */}
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[760px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="sticky left-0 bg-[var(--bg)] px-3 py-2">Клиника</th>
              <th className="px-3 py-2">Цена</th>
              <th className="px-3 py-2">Город</th>
              <th className="px-3 py-2">Рейтинг</th>
              <th className="px-3 py-2">Онлайн-запись</th>
              <th className="px-3 py-2">Обновлено</th>
              <th className="px-3 py-2">Источник</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {offers.map((o) => (
              <tr key={o.price_id} className={`bg-white ${o.is_cheapest ? "ring-2 ring-teal-300" : ""}`}>
                <td className="sticky left-0 bg-white px-3 py-3 font-semibold text-ink">
                  <Link href={`/clinics/${o.clinic_id}`} className="hover:text-brand-700">
                    {o.clinic_name}
                  </Link>
                  {o.is_cheapest && <span className="ml-2 chip bg-teal-100 text-teal-700">дешевле всех</span>}
                </td>
                <td className="px-3 py-3 text-lg font-bold text-ink">{formatKzt(o.price_kzt)}</td>
                <td className="px-3 py-3 text-slate-600">{o.city}</td>
                <td className="px-3 py-3">
                  {o.rating != null ? (
                    <span className="inline-flex items-center gap-1 text-amber-600">
                      <Star size={13} className="fill-amber-400 text-amber-400" /> {o.rating.toFixed(1)}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-3 py-3">
                  {o.has_online_booking ? (
                    <CalendarCheck size={16} className="text-emerald-600" />
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
                <td className="px-3 py-3 text-slate-500">{relativeDays(o.parsed_at)}</td>
                <td className="px-3 py-3 text-slate-500">{o.source}</td>
                <td className="px-3 py-3">
                  <a href={o.source_url || o.website} target="_blank" rel="noopener noreferrer" className="btn-outline px-2.5 py-1.5">
                    <ExternalLink size={14} />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* History */}
      <div className="card mt-8 p-6">
        <h2 className="mb-3 text-lg font-bold text-ink">История изменения цен</h2>
        {history ? <PriceHistoryChart data={history} /> : <p className="text-slate-400">Загрузка…</p>}
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="container-page py-20 text-center text-slate-400">Загрузка…</div>}>
      <CompareContent />
    </Suspense>
  );
}
