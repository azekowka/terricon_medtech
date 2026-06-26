"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Loader2, MapPin, Users } from "lucide-react";
import { api } from "@/lib/api";
import type { DoctorCard as Doctor, DoctorsMeta, DoctorsResult } from "@/lib/types";
import { DoctorCard } from "@/components/doctors/DoctorCard";
import { DoctorFilters, DocFilterState } from "@/components/doctors/DoctorFilters";
import { RegionPopup } from "@/components/doctors/RegionPopup";
import { pluralRu } from "@/lib/format";

const DEFAULT_FILTERS: DocFilterState = {
  specialty: "",
  price_max: "",
  rating_min: "",
  experience_min: "",
  accepts_children: false,
  online_booking: false,
  verified: false,
  sort: "rating",
};

export default function DoctorsPage() {
  const [meta, setMeta] = useState<DoctorsMeta | null>(null);
  const [region, setRegion] = useState<string>("almaty");
  const [showPopup, setShowPopup] = useState(false);
  const [filters, setFilters] = useState<DocFilterState>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<DoctorsResult | null>(null);
  const [loading, setLoading] = useState(true);

  // load meta + restore saved region
  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("doctor_region") : null;
    api.doctorsMeta().then((m) => {
      setMeta(m);
      if (saved && m.regions.some((r) => r.slug === saved)) setRegion(saved);
      else if (m.regions.length && !m.regions.some((r) => r.slug === "almaty")) setRegion(m.regions[0].slug);
    });
  }, []);

  const onChange = useCallback((patch: Partial<DocFilterState>) => {
    setFilters((s) => ({ ...s, ...patch }));
    setPage(1);
  }, []);

  // fetch doctors on region/filter/page change (debounced)
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params: Record<string, any> = {
      region,
      specialty: filters.specialty || undefined,
      price_max: filters.price_max || undefined,
      rating_min: filters.rating_min || undefined,
      experience_min: filters.experience_min || undefined,
      accepts_children: filters.accepts_children || undefined,
      online_booking: filters.online_booking || undefined,
      verified: filters.verified || undefined,
      sort: filters.sort,
      page,
      page_size: 15,
    };
    const t = setTimeout(() => {
      api
        .doctors(params)
        .then((r) => !cancelled && setResult(r))
        .catch(() => !cancelled && setResult(null))
        .finally(() => !cancelled && setLoading(false));
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [region, filters, page]);

  function selectRegion(slug: string) {
    setRegion(slug);
    setPage(1);
    setShowPopup(false);
    if (typeof window !== "undefined") localStorage.setItem("doctor_region", slug);
  }

  const regionName = meta?.regions.find((r) => r.slug === region)?.name || "Казахстан";
  const regionCount = meta?.regions.find((r) => r.slug === region)?.count || 0;
  const clinicsApprox = result?.total ? Math.max(1, Math.round(result.total / 3)) : 0;

  return (
    <div className="container-page pt-6">
      {/* header */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-ink sm:text-3xl">Врачи-специалисты в {regionName}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {loading ? "Загрузка…" : (
              <>
                {result?.total ?? 0} {pluralRu(result?.total ?? 0, ["врач", "врача", "врачей"])}
                {filters.specialty ? " по фильтру" : ` · ${regionCount} в городе`}
              </>
            )}
          </p>
        </div>
        <button onClick={() => setShowPopup(true)} className="btn-outline self-start">
          <MapPin size={16} /> {regionName} <span className="text-slate-400">· сменить</span>
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <aside>
          {meta && <DoctorFilters specialties={meta.specialties} state={filters} onChange={onChange} />}
        </aside>

        <section className="space-y-3 pb-10">
          {loading ? (
            <div className="flex items-center justify-center py-24 text-slate-400">
              <Loader2 className="animate-spin" />
            </div>
          ) : result && result.doctors.length > 0 ? (
            <>
              {result.doctors.map((doc) => (
                <DoctorCard key={doc.id} doctor={doc} />
              ))}
              {result.pages > 1 && (
                <Pagination page={result.page} pages={result.pages} onPage={setPage} />
              )}
            </>
          ) : (
            <div className="card flex flex-col items-center gap-2 p-12 text-center text-slate-500">
              <Users size={32} className="text-slate-300" />
              <p className="text-lg font-semibold text-ink">Врачи не найдены</p>
              <p className="text-sm">Измените фильтры или выберите другой город.</p>
            </div>
          )}
        </section>
      </div>

      {showPopup && meta && (
        <RegionPopup regions={meta.regions} current={region} onSelect={selectRegion} onClose={() => setShowPopup(false)} />
      )}
    </div>
  );
}

function Pagination({ page, pages, onPage }: { page: number; pages: number; onPage: (p: number) => void }) {
  const window = useMemo(() => {
    const start = Math.max(1, Math.min(page - 2, pages - 4));
    const end = Math.min(pages, start + 4);
    const arr = [];
    for (let i = start; i <= end; i++) arr.push(i);
    return arr;
  }, [page, pages]);
  return (
    <div className="flex items-center justify-center gap-1 pt-4">
      <button disabled={page <= 1} onClick={() => onPage(page - 1)} className="btn-outline px-2.5 py-2 disabled:opacity-40">
        <ChevronLeft size={16} />
      </button>
      {window[0] > 1 && (
        <>
          <PageBtn n={1} page={page} onPage={onPage} />
          <span className="px-1 text-slate-400">…</span>
        </>
      )}
      {window.map((n) => (
        <PageBtn key={n} n={n} page={page} onPage={onPage} />
      ))}
      {window[window.length - 1] < pages && (
        <>
          <span className="px-1 text-slate-400">…</span>
          <PageBtn n={pages} page={page} onPage={onPage} />
        </>
      )}
      <button disabled={page >= pages} onClick={() => onPage(page + 1)} className="btn-outline px-2.5 py-2 disabled:opacity-40">
        <ChevronRight size={16} />
      </button>
    </div>
  );
}

function PageBtn({ n, page, onPage }: { n: number; page: number; onPage: (p: number) => void }) {
  return (
    <button
      onClick={() => onPage(n)}
      className={`h-10 min-w-10 rounded-xl px-3 text-sm font-semibold transition ${
        n === page ? "bg-brand-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
      }`}
    >
      {n}
    </button>
  );
}
