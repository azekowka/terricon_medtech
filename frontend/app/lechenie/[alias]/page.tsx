"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, HeartPulse, MapPin, Stethoscope } from "lucide-react";
import { api } from "@/lib/api";
import type { DoctorRegion, IllnessDetail } from "@/lib/types";
import { DoctorCard } from "@/components/doctors/DoctorCard";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { pluralRu } from "@/lib/format";

export default function IllnessPage({ params }: { params: { alias: string } }) {
  const { t } = useI18n();
  const { alias } = params;
  const [d, setD] = useState<IllnessDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [regions, setRegions] = useState<DoctorRegion[]>([]);
  const [region, setRegion] = useState<string>("almaty");

  // city list for the selector + restore saved city
  useEffect(() => {
    const saved = (typeof window !== "undefined" && localStorage.getItem("doctor_region")) || "almaty";
    setRegion(saved);
    api.doctorsMeta().then((m) => setRegions(m.regions)).catch(() => setRegions([]));
  }, []);

  function changeCity(slug: string) {
    setRegion(slug);
    try {
      if (slug) localStorage.setItem("doctor_region", slug);
    } catch {}
  }

  useEffect(() => {
    setLoading(true);
    api.illness(alias, region || undefined).then(setD).catch(() => setD(null)).finally(() => setLoading(false));
  }, [alias, region]);

  if (loading && !d) {
    return (
      <div className="container-page flex flex-col items-center gap-3 py-28 text-slate-400">
        <HeartPulse className="animate-pulse" size={34} />
        <p>{t("common.loading")}</p>
      </div>
    );
  }
  if (!d) {
    return (
      <div className="container-page py-28 text-center">
        <p className="text-xl font-bold text-ink">{t("lech.notFound")}</p>
        <Link href="/lechenie" className="btn-primary mt-6">{t("lech.toCatalog")}</Link>
      </div>
    );
  }

  return (
    <div className="container-page pt-6">
      <Link href="/lechenie" className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-700">
        <ArrowLeft size={16} /> {t("lech.toCatalog")}
      </Link>

      {/* header */}
      <div className="card p-6">
        <div className="flex items-start gap-3">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
            <HeartPulse size={24} />
          </span>
          <div>
            <h1 className="text-2xl font-extrabold text-ink">{d.name}</h1>
            {d.skills.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <span className="text-sm text-slate-500">{t("lech.treatedBy")}:</span>
                {d.skills.map((s) => (
                  <span key={s.alias} className="chip bg-brand-50 text-brand-700">
                    <Stethoscope size={12} /> {s.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* doctors who treat it */}
      <div className="mt-6">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-bold text-ink">
            {t("lech.whoTreats")}{" "}
            <span className="text-slate-400">
              ({d.doctors_total} {pluralRu(d.doctors_total, ["врач", "врача", "врачей"])})
            </span>
          </h2>
          <div className="relative">
            <MapPin size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={region}
              onChange={(e) => changeCity(e.target.value)}
              className="input w-full py-2 pl-9 sm:w-56"
            >
              <option value="">{t("search.allCities")}</option>
              {regions.map((r) => (
                <option key={r.slug} value={r.slug}>
                  {r.name} ({r.count})
                </option>
              ))}
            </select>
          </div>
        </div>
        {d.doctors.length > 0 ? (
          <div className={`space-y-3 transition ${loading ? "pointer-events-none opacity-50" : ""}`}>
            {d.doctors.map((doc) => (
              <DoctorCard key={doc.id} doctor={doc} />
            ))}
          </div>
        ) : (
          <p className="card p-8 text-center text-slate-500">{t("doctors.notFound")}</p>
        )}
      </div>

      {/* related diseases */}
      {d.similar.length > 0 && (
        <div className="card mt-6 p-6">
          <h2 className="mb-3 text-lg font-bold text-ink">{t("lech.related")}</h2>
          <div className="flex flex-wrap gap-2">
            {d.similar.map((s) => (
              <Link key={s.alias} href={`/lechenie/${s.alias}`} className="chip bg-slate-100 text-slate-600 hover:bg-brand-50 hover:text-brand-700">
                {s.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
