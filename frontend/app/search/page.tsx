"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { GitCompareArrows, Loader2, LineChart } from "lucide-react";
import { api } from "@/lib/api";
import type { Meta, Offer, SearchResult } from "@/lib/types";
import { SearchBar } from "@/components/SearchBar";
import { Filters, FilterState } from "@/components/Filters";
import { OfferCard } from "@/components/OfferCard";
import { SubscribeModal } from "@/components/SubscribeModal";
import { formatKzt, categoryMeta } from "@/lib/format";

function SearchContent() {
  const params = useSearchParams();
  const router = useRouter();
  const serviceId = params.get("service_id") || undefined;
  const q = params.get("q") || undefined;
  const nameParam = params.get("name") || undefined;
  const categoryParam = params.get("category") || "";

  const [meta, setMeta] = useState<Meta | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [geo, setGeo] = useState<{ lat: number; lng: number } | null>(null);
  const [subTarget, setSubTarget] = useState<Offer | null>(null);

  const [state, setState] = useState<FilterState>({
    city: "",
    category: categoryParam,
    price_min: "",
    price_max: "",
    rating_min: "",
    online_booking: false,
    include_stale: false,
    sort: "price_asc",
  });

  const onChange = useCallback((patch: Partial<FilterState>) => {
    setState((s) => ({ ...s, ...patch }));
  }, []);

  useEffect(() => {
    api.meta().then(setMeta).catch(() => setMeta(null));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const query: Record<string, any> = {
      service_id: serviceId,
      q,
      city: state.city || undefined,
      category: state.category || undefined,
      price_min: state.price_min || undefined,
      price_max: state.price_max || undefined,
      rating_min: state.rating_min || undefined,
      online_booking: state.online_booking || undefined,
      include_stale: state.include_stale || undefined,
      sort: state.sort,
      lat: geo?.lat,
      lng: geo?.lng,
    };
    // debounce so typing in the price fields doesn't fire a request per keystroke
    const timer = setTimeout(() => {
      api
        .search(query)
        .then((r) => {
          if (!cancelled) setResult(r);
        })
        .catch(() => !cancelled && setResult(null))
        .finally(() => !cancelled && setLoading(false));
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [serviceId, q, state, geo]);

  function locate() {
    if (geo) {
      setGeo(null);
      return;
    }
    navigator.geolocation?.getCurrentPosition(
      (pos) => {
        setGeo({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        onChange({ sort: "distance" });
      },
      () => alert("Не удалось получить геолокацию"),
    );
  }

  function toggleCompare(clinicId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(clinicId) ? next.delete(clinicId) : next.add(clinicId);
      return next;
    });
  }

  const title = result?.service?.name || nameParam || q || "Результаты поиска";
  const stats = result?.stats;
  const cm = result?.service ? categoryMeta(result.service.category) : null;
  const CatIcon = cm?.icon;

  const goCompare = () => {
    if (!result?.service) return;
    const ids = Array.from(selected).join(",");
    router.push(`/compare?service_id=${result.service.id}&clinic_ids=${ids}`);
  };

  return (
    <div className="container-page pt-6">
      <div className="mb-5 max-w-2xl">
        <SearchBar size="md" initialValue={nameParam || q || ""} />
      </div>

      {/* Heading + price stats */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            {cm && CatIcon && (
              <span className={`chip ${cm.chip}`}>
                <CatIcon size={12} strokeWidth={2} /> {cm.label}
              </span>
            )}
            <h1 className="text-2xl font-bold tracking-tight text-ink">{title}</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            {loading ? "Загрузка…" : `Найдено ${stats?.count ?? 0} предложений`}
            {result?.service?.specialty && ` · ${result.service.specialty}`}
            {result?.service?.duration_days != null && ` · срок ${result.service.duration_days} дн.`}
            {result?.service?.tarif_code && ` · код ${result.service.tarif_code}`}
          </p>
        </div>
        {stats && stats.count > 0 && (
          <div className="flex gap-2">
            <PriceStat label="мин." value={stats.min_price} highlight />
            <PriceStat label="средн." value={stats.avg_price} />
            <PriceStat label="макс." value={stats.max_price} />
            {result?.service && (
              <Link href={`/compare?service_id=${result.service.id}`} className="btn-outline">
                <LineChart size={16} /> История
              </Link>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="min-w-0">
          <Filters
            meta={meta}
            state={state}
            onChange={onChange}
            lockedCategory={!!result?.service}
            onLocate={locate}
            geoEnabled={!!geo}
          />
        </aside>

        <section className="min-w-0 space-y-3 pb-24">
          {loading ? (
            <div className="flex items-center justify-center py-20 text-slate-400">
              <Loader2 className="animate-spin" />
            </div>
          ) : result && result.offers.length > 0 ? (
            (() => {
              const minPrice = Math.min(...result.offers.map((o) => o.price_kzt));
              let flagged = false;
              return result.offers.map((o) => {
                const isCheapest = !flagged && o.price_kzt === minPrice;
                if (isCheapest) flagged = true;
                return (
                  <OfferCard
                    key={o.price_id}
                    offer={o}
                    isCheapest={isCheapest}
                    subscribable={!!result.service}
                    selected={selected.has(o.clinic_id)}
                    onToggleCompare={() => toggleCompare(o.clinic_id)}
                    onSubscribe={() => setSubTarget(o)}
                  />
                );
              });
            })()
          ) : (
            <div className="card p-10 text-center text-slate-500">
              <p className="text-lg font-semibold text-ink">Ничего не найдено</p>
              <p className="mt-1 text-sm">Попробуйте изменить фильтры или уточнить запрос.</p>
            </div>
          )}
        </section>
      </div>

      {/* Compare sticky bar */}
      {selected.size > 0 && result?.service && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 backdrop-blur">
          <div className="container-page flex items-center justify-between py-3">
            <span className="text-sm font-medium text-slate-600">
              Выбрано клиник для сравнения: <b>{selected.size}</b>
            </span>
            <div className="flex gap-2">
              <button onClick={() => setSelected(new Set())} className="btn-ghost">
                Сбросить
              </button>
              <button onClick={goCompare} className="btn-primary">
                <GitCompareArrows size={16} /> Сравнить
              </button>
            </div>
          </div>
        </div>
      )}

      {subTarget && result && (
        <SubscribeModal
          serviceId={result.service?.id || ""}
          serviceName={title}
          clinic={{ id: subTarget.clinic_id, name: subTarget.clinic_name, price: subTarget.price_kzt }}
          onClose={() => setSubTarget(null)}
        />
      )}
    </div>
  );
}

function PriceStat({ label, value, highlight }: { label: string; value: number | null | undefined; highlight?: boolean }) {
  return (
    <div className={`rounded-xl px-3 py-2 text-center ${highlight ? "bg-teal-50" : "bg-slate-50"}`}>
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className={`text-sm font-bold ${highlight ? "text-teal-700" : "text-ink"}`}>{formatKzt(value)}</div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="container-page py-20 text-center text-slate-400">Загрузка…</div>}>
      <SearchContent />
    </Suspense>
  );
}
