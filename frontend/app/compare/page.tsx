"use client";

import { Fragment, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CalendarCheck, ChevronDown, ChevronRight, ExternalLink, Search, Star } from "lucide-react";
import { api } from "@/lib/api";
import type { HistorySeries, Offer, SearchResult, ServiceItem } from "@/lib/types";
import { SearchBar } from "@/components/SearchBar";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { formatKzt, relativeDays, categoryMeta, pluralRu } from "@/lib/format";

function CompareContent() {
  const params = useSearchParams();
  const serviceId = params.get("service_id") || "";
  const clinicIds = params.get("clinic_ids") || "";

  const [result, setResult] = useState<SearchResult | null>(null);
  const [history, setHistory] = useState<HistorySeries | null>(null);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");

  useEffect(() => {
    // all services that actually have clinic prices to compare
    api.services({ limit: 2000 }).then((all) => setServices(all.filter((s) => s.offers_count > 0))).catch(() => {});
  }, []);

  const catCounts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const s of services) m[s.category] = (m[s.category] || 0) + 1;
    return m;
  }, [services]);

  const filteredServices = useMemo(() => {
    const nq = q.trim().toLowerCase();
    return services
      .filter((s) => (!cat || s.category === cat) && (!nq || s.name.toLowerCase().includes(nq)))
      .sort((a, b) => b.offers_count - a.offers_count);
  }, [services, q, cat]);

  // ---- results filters + sorting (client-side over the offers for one service) ----
  const [fCity, setFCity] = useState("");
  const [fSource, setFSource] = useState("");
  const [fPriceMax, setFPriceMax] = useState("");
  const [fRatingMin, setFRatingMin] = useState("");
  const [fOnline, setFOnline] = useState(false);
  const [sortField, setSortField] = useState<"price" | "rating" | "updated" | "city" | "source">("price");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const rawOffers = result?.offers || [];
  const offerCities = useMemo(() => [...new Set(rawOffers.map((o) => o.city))].sort(), [rawOffers]);
  const offerSources = useMemo(() => [...new Set(rawOffers.map((o) => o.source))].sort(), [rawOffers]);

  const displayOffers = useMemo(() => {
    let list = rawOffers.filter(
      (o) =>
        (!fCity || o.city === fCity) &&
        (!fSource || o.source === fSource) &&
        (!fPriceMax || o.price_kzt <= Number(fPriceMax)) &&
        (!fRatingMin || (o.rating ?? 0) >= Number(fRatingMin)) &&
        (!fOnline || o.has_online_booking),
    );
    const dir = sortDir === "asc" ? 1 : -1;
    list = [...list].sort((a, b) => {
      switch (sortField) {
        case "rating":
          return ((a.rating ?? -1) - (b.rating ?? -1)) * dir;
        case "updated":
          return (new Date(a.parsed_at).getTime() - new Date(b.parsed_at).getTime()) * dir;
        case "city":
          return a.city.localeCompare(b.city) * dir;
        case "source":
          return a.source.localeCompare(b.source) * dir;
        default:
          return (a.price_kzt - b.price_kzt) * dir;
      }
    });
    return list;
  }, [rawOffers, fCity, fSource, fPriceMax, fRatingMin, fOnline, sortField, sortDir]);

  function toggleSort(field: typeof sortField) {
    if (sortField === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortField(field);
      setSortDir(field === "rating" || field === "updated" ? "desc" : "asc");
    }
  }

  // ---- group offers into clinic chains; branches collapse under the brand ----
  const cheapest = displayOffers.length ? Math.min(...displayOffers.map((o) => o.price_kzt)) : null;
  const chainGroups = useMemo(() => {
    const map = new Map<string, { key: string; chain: string; offers: Offer[] }>();
    for (const o of displayOffers) {
      const k = o.source || o.clinic_name;
      if (!map.has(k)) map.set(k, { key: k, chain: chainName(o.clinic_name), offers: [] });
      map.get(k)!.offers.push(o);
    }
    // Map preserves first-occurrence order, so groups inherit the active global sort.
    return [...map.values()];
  }, [displayOffers]);

  const [openChains, setOpenChains] = useState<Set<string>>(new Set());
  useEffect(() => {
    // default-open the cheapest MULTI-branch chain (so something useful is shown)
    const offers = result?.offers || [];
    if (!offers.length) return setOpenChains(new Set());
    const bySrc = new Map<string, Offer[]>();
    for (const o of offers) {
      const k = o.source || o.clinic_name;
      if (!bySrc.has(k)) bySrc.set(k, []);
      bySrc.get(k)!.push(o);
    }
    const multi = [...bySrc.entries()].filter(([, v]) => v.length > 1);
    if (!multi.length) return setOpenChains(new Set());
    multi.sort(
      (a, b) => Math.min(...a[1].map((o) => o.price_kzt)) - Math.min(...b[1].map((o) => o.price_kzt)),
    );
    setOpenChains(new Set([multi[0][0]]));
  }, [serviceId, result]);
  const toggleChain = (k: string) =>
    setOpenChains((s) => {
      const n = new Set(s);
      n.has(k) ? n.delete(k) : n.add(k);
      return n;
    });

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
    const CATS = [
      { key: "", label: "Все" },
      { key: "laboratory", label: "Лаборатория" },
      { key: "doctor", label: "Приём врача" },
      { key: "diagnostic", label: "Диагностика" },
      { key: "procedure", label: "Процедура" },
    ];
    return (
      <div className="container-page pt-8">
        <h1 className="text-2xl font-extrabold text-ink">Сравнение цен</h1>
        <p className="mt-2 text-slate-500">
          Выберите услугу, чтобы сравнить цены клиник. Доступно{" "}
          <b className="text-ink">{services.length}</b> услуг с ценами.
        </p>
        <div className="mt-5 max-w-2xl">
          <SearchBar size="md" />
        </div>

        {/* category filter */}
        <div className="mt-6 flex flex-wrap gap-2">
          {CATS.map((c) => {
            const count = c.key ? catCounts[c.key] || 0 : services.length;
            return (
              <button
                key={c.key}
                onClick={() => setCat(c.key)}
                className={`chip text-sm transition ${cat === c.key ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
              >
                {c.label} <span className="opacity-60">{count}</span>
              </button>
            );
          })}
        </div>

        {/* in-list search */}
        <div className="relative mt-4 max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Фильтр по названию услуги…"
            className="input pl-10"
          />
        </div>

        <p className="mt-3 text-sm text-slate-400">Найдено: {filteredServices.length}</p>
        <div className="mt-2 grid max-h-[60vh] gap-2 overflow-y-auto pr-1 sm:grid-cols-2 lg:grid-cols-3">
          {filteredServices.slice(0, 400).map((s) => {
            const cm = categoryMeta(s.category);
            const Icon = cm.icon;
            return (
              <Link
                key={s.id}
                href={`/compare?service_id=${s.id}`}
                className="card flex items-center justify-between gap-3 p-3.5 transition duration-200 hover:-translate-y-0.5 hover:shadow-hover"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${cm.color}`}>
                    <Icon size={16} strokeWidth={1.75} />
                  </span>
                  <span className="truncate font-semibold text-ink">{s.name}</span>
                </span>
                <span className="shrink-0 rounded-md bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-500">
                  {s.offers_count}
                </span>
              </Link>
            );
          })}
        </div>
        {filteredServices.length > 400 && (
          <p className="mt-3 text-center text-sm text-slate-400">
            Показаны первые 400 — уточните поиск или категорию
          </p>
        )}
      </div>
    );
  }

  const hasFilters = fCity || fSource || fPriceMax || fRatingMin || fOnline;
  const arrow = (f: typeof sortField) => (sortField === f ? (sortDir === "asc" ? " ↑" : " ↓") : "");

  return (
    <div className="container-page pt-6">
      <div className="mb-5 max-w-2xl">
        <SearchBar size="md" initialValue={result?.service?.name || ""} />
      </div>

      <h1 className="text-2xl font-extrabold text-ink">
        Сравнение: {result?.service?.name || "услуга"}
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        {loading
          ? "Загрузка…"
          : `Показано ${displayOffers.length} из ${rawOffers.length} · разница цен до ${formatKzt(
              (result?.stats?.max_price || 0) - (result?.stats?.min_price || 0),
            )}`}
      </p>

      {/* Filters */}
      <div className="mt-4 flex flex-wrap items-end gap-3 rounded-2xl border border-slate-100 bg-white p-3 shadow-card">
        <Field label="Город">
          <select className="input py-2" value={fCity} onChange={(e) => setFCity(e.target.value)}>
            <option value="">Все города</option>
            {offerCities.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </Field>
        <Field label="Источник">
          <select className="input py-2" value={fSource} onChange={(e) => setFSource(e.target.value)}>
            <option value="">Все</option>
            {offerSources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </Field>
        <Field label="Цена до, ₸">
          <input
            type="number"
            className="input w-32 py-2"
            placeholder="напр. 5000"
            value={fPriceMax}
            onChange={(e) => setFPriceMax(e.target.value)}
          />
        </Field>
        <Field label="Рейтинг от">
          <select className="input py-2" value={fRatingMin} onChange={(e) => setFRatingMin(e.target.value)}>
            <option value="">Любой</option>
            <option value="4">4.0 ★</option>
            <option value="4.3">4.3 ★</option>
            <option value="4.5">4.5 ★</option>
          </select>
        </Field>
        <label className="flex cursor-pointer items-center gap-2 rounded-xl bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700">
          <input type="checkbox" checked={fOnline} onChange={(e) => setFOnline(e.target.checked)} className="h-4 w-4" />
          Онлайн-запись
        </label>
        {hasFilters && (
          <button
            onClick={() => { setFCity(""); setFSource(""); setFPriceMax(""); setFRatingMin(""); setFOnline(false); }}
            className="btn-ghost py-2"
          >
            Сбросить
          </button>
        )}
      </div>

      {/* Comparison table (sortable headers) */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[820px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="sticky left-0 bg-[var(--bg)] px-3 py-2">Клиника</th>
              <SortableTh label={`Цена${arrow("price")}`} onClick={() => toggleSort("price")} active={sortField === "price"} />
              <SortableTh label={`Город${arrow("city")}`} onClick={() => toggleSort("city")} active={sortField === "city"} />
              <SortableTh label={`Рейтинг${arrow("rating")}`} onClick={() => toggleSort("rating")} active={sortField === "rating"} />
              <th className="px-3 py-2">Онлайн-запись</th>
              <SortableTh label={`Обновлено${arrow("updated")}`} onClick={() => toggleSort("updated")} active={sortField === "updated"} />
              <SortableTh label={`Источник${arrow("source")}`} onClick={() => toggleSort("source")} active={sortField === "source"} />
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {chainGroups.map((g) => {
              // standalone clinic (single offer) -> plain row, no accordion
              if (g.offers.length === 1) {
                const o = g.offers[0];
                const isCheapest = o.price_kzt === cheapest;
                return (
                  <tr key={g.key} className={`bg-white ${isCheapest ? "ring-2 ring-teal-300" : ""}`}>
                    <td className="sticky left-0 bg-white px-3 py-3 font-semibold text-ink">
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-block w-4 shrink-0" />
                        <Link href={`/clinics/${o.clinic_id}`} className="hover:text-brand-700">{o.clinic_name}</Link>
                        {isCheapest && <span className="chip bg-teal-100 text-teal-700">дешевле всех</span>}
                      </span>
                    </td>
                    <OfferCells o={o} />
                  </tr>
                );
              }
              // clinic chain with several branches -> collapsible parent
              const open = openChains.has(g.key);
              const prices = g.offers.map((o) => o.price_kzt);
              const gMin = Math.min(...prices);
              const cities = [...new Set(g.offers.map((o) => o.city))];
              const bestRating = Math.max(...g.offers.map((o) => o.rating ?? -1));
              const anyOnline = g.offers.some((o) => o.has_online_booking);
              const latest = g.offers.reduce((a, b) =>
                new Date(b.parsed_at) > new Date(a.parsed_at) ? b : a,
              ).parsed_at;
              const groupHasCheapest = cheapest != null && prices.includes(cheapest);
              return (
                <Fragment key={g.key}>
                  <tr
                    onClick={() => toggleChain(g.key)}
                    className={`cursor-pointer bg-slate-50 hover:bg-slate-100 ${
                      groupHasCheapest && !open ? "ring-2 ring-teal-300" : ""
                    }`}
                  >
                    <td className="sticky left-0 bg-slate-50 px-3 py-3 font-bold text-ink">
                      <span className="inline-flex items-center gap-2">
                        <span className="text-slate-400">
                          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </span>
                        <span>{g.chain}</span>
                        <span className="chip bg-slate-200 text-[11px] text-slate-600">
                          {g.offers.length} {pluralRu(g.offers.length, ["филиал", "филиала", "филиалов"])}
                        </span>
                      </span>
                    </td>
                    <td className="px-3 py-3 text-lg font-bold text-ink">от {formatKzt(gMin)}</td>
                    <td className="px-3 py-3 text-slate-600">
                      {cities.length === 1
                        ? cities[0]
                        : `${cities.length} ${pluralRu(cities.length, ["город", "города", "городов"])}`}
                    </td>
                    <td className="px-3 py-3">
                      {bestRating >= 0 ? (
                        <span className="inline-flex items-center gap-1 text-amber-600">
                          <Star size={13} className="fill-amber-400 text-amber-400" /> {bestRating.toFixed(1)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-3">
                      {anyOnline ? (
                        <CalendarCheck size={16} className="text-emerald-600" />
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-slate-500">{relativeDays(latest)}</td>
                    <td className="px-3 py-3 text-slate-500">{g.key}</td>
                    <td className="px-3 py-3 text-right text-xs font-medium text-brand-600">
                      {open ? "Свернуть" : "Развернуть"}
                    </td>
                  </tr>
                  {open &&
                    g.offers.map((o) => {
                      const isCheapest = o.price_kzt === cheapest;
                      return (
                        <tr key={o.price_id} className={`bg-white ${isCheapest ? "ring-2 ring-teal-300" : ""}`}>
                          <td className="sticky left-0 bg-white py-2.5 pl-10 pr-3 text-slate-700">
                            <Link href={`/clinics/${o.clinic_id}`} className="font-medium hover:text-brand-700">
                              {branchName(o.clinic_name)}
                            </Link>
                            {isCheapest && <span className="ml-2 chip bg-teal-100 text-teal-700">дешевле всех</span>}
                          </td>
                          <OfferCells o={o} />
                        </tr>
                      );
                    })}
                </Fragment>
              );
            })}
            {chainGroups.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-10 text-center text-slate-400">
                  Нет предложений по выбранным фильтрам
                </td>
              </tr>
            )}
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

// "Медцентр Olymp — Гагарина" -> chain "Медцентр Olymp", branch "Гагарина"
function splitChain(name: string): [string, string] {
  const parts = name.split(/\s+[—–-]\s+/);
  return parts.length > 1 ? [parts[0].trim(), parts.slice(1).join(" — ").trim()] : [name.trim(), name.trim()];
}
function chainName(name: string) {
  return splitChain(name)[0];
}
function branchName(name: string) {
  return splitChain(name)[1];
}

/** The 7 per-offer data cells (price → source link), shared by single & branch rows. */
function OfferCells({ o }: { o: Offer }) {
  return (
    <>
      <td className="px-3 py-2.5 text-base font-bold text-ink">{formatKzt(o.price_kzt)}</td>
      <td className="px-3 py-2.5 text-slate-600">{o.city}</td>
      <td className="px-3 py-2.5">
        {o.rating != null ? (
          <span className="inline-flex items-center gap-1 text-amber-600">
            <Star size={13} className="fill-amber-400 text-amber-400" /> {o.rating.toFixed(1)}
          </span>
        ) : (
          "—"
        )}
      </td>
      <td className="px-3 py-2.5">
        {o.has_online_booking ? (
          <CalendarCheck size={16} className="text-emerald-600" />
        ) : (
          <span className="text-slate-300">—</span>
        )}
      </td>
      <td className="px-3 py-2.5 text-slate-500">{relativeDays(o.parsed_at)}</td>
      <td className="px-3 py-2.5 text-slate-500">{o.source}</td>
      <td className="px-3 py-2.5">
        <a href={o.source_url || o.website} target="_blank" rel="noopener noreferrer" className="btn-outline px-2.5 py-1.5">
          <ExternalLink size={14} />
        </a>
      </td>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</label>
      {children}
    </div>
  );
}

function SortableTh({ label, onClick, active }: { label: string; onClick: () => void; active: boolean }) {
  return (
    <th className="px-3 py-2">
      <button
        onClick={onClick}
        className={`-mx-1 rounded px-1 uppercase transition hover:text-brand-600 ${active ? "text-brand-600" : ""}`}
      >
        {label}
      </button>
    </th>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="container-page py-20 text-center text-slate-400">Загрузка…</div>}>
      <CompareContent />
    </Suspense>
  );
}
