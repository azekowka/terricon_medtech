"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight, HeartPulse, Search, Stethoscope, X } from "lucide-react";
import { api } from "@/lib/api";
import type { DiseaseRef, IllnessCategories, IllnessCategory } from "@/lib/types";
import { useI18n } from "@/lib/i18n/I18nProvider";

export default function LecheniePage() {
  const { t } = useI18n();
  const [data, setData] = useState<IllnessCategories | null>(null);
  const [q, setQ] = useState("");
  const [openCat, setOpenCat] = useState<IllnessCategory | null>(null);

  useEffect(() => {
    api.illnessCategories().then(setData).catch(() => setData(null));
  }, []);

  // flat unique disease list for search
  const allDiseases = useMemo(() => {
    if (!data) return [];
    const m = new Map<string, DiseaseRef>();
    for (const c of data.categories) for (const d of c.diseases) m.set(d.alias, d);
    return [...m.values()].sort((a, b) => a.name.localeCompare(b.name));
  }, [data]);

  const searchResults = useMemo(() => {
    const nq = q.trim().toLowerCase();
    if (!nq) return [];
    return allDiseases.filter((d) => d.name.toLowerCase().includes(nq)).slice(0, 60);
  }, [q, allDiseases]);

  return (
    <div className="container-page pt-6">
      <div className="mb-1 flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
          <HeartPulse size={20} />
        </span>
        <h1 className="text-2xl font-extrabold text-ink sm:text-3xl">{t("lech.title")}</h1>
      </div>
      <p className="mb-5 text-sm text-slate-500">
        {t("lech.subtitle")} {data ? `${data.total_diseases} ${t("lech.diseases")}.` : ""}
      </p>

      <div className="relative mb-6 max-w-xl">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("lech.search")}
          className="input pl-11"
        />
      </div>

      {q.trim() ? (
        <>
          <p className="mb-3 text-sm text-slate-400">{t("lech.found")}: {searchResults.length}</p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {searchResults.map((d) => (
              <DiseaseLink key={d.alias} d={d} />
            ))}
          </div>
        </>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data?.categories.map((c) => (
            <button
              key={c.alias}
              onClick={() => setOpenCat(c)}
              className="card group flex items-center justify-between gap-3 p-4 text-left transition hover:-translate-y-0.5 hover:shadow-hover"
            >
              <span className="flex min-w-0 items-center gap-3">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <Stethoscope size={20} />
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-ink group-hover:text-brand-700">{c.name}</span>
                  <span className="text-xs text-slate-400">{c.count} {t("lech.diseases")}</span>
                </span>
              </span>
              <ChevronRight size={18} className="shrink-0 text-slate-300 group-hover:text-brand-500" />
            </button>
          ))}
        </div>
      )}

      {/* diseases in a category (picture 2) */}
      {openCat && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/40 p-4 py-12" onClick={() => setOpenCat(null)}>
          <div className="card w-full max-w-2xl p-6" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <Stethoscope size={20} />
                </span>
                <div>
                  <h2 className="text-lg font-bold text-ink">{openCat.name}</h2>
                  <p className="text-xs text-slate-400">{openCat.count} {t("lech.diseases")}</p>
                </div>
              </div>
              <button onClick={() => setOpenCat(null)} className="text-slate-400 hover:text-slate-700">
                <X size={22} />
              </button>
            </div>
            <div className="grid max-h-[60vh] gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
              {openCat.diseases.map((d) => (
                <DiseaseLink key={d.alias} d={d} onClick={() => setOpenCat(null)} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DiseaseLink({ d, onClick }: { d: DiseaseRef; onClick?: () => void }) {
  return (
    <Link
      href={`/lechenie/${d.alias}`}
      onClick={onClick}
      className="flex items-center justify-between gap-2 rounded-xl border border-slate-100 bg-white px-3.5 py-2.5 text-sm transition hover:border-brand-300 hover:bg-brand-50/40"
    >
      <span className="truncate font-medium text-ink">{d.name}</span>
      <ChevronRight size={15} className="shrink-0 text-slate-300" />
    </Link>
  );
}
