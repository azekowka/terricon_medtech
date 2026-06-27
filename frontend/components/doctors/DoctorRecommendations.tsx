"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, Star, TrendingDown, Award, Flame, Gem } from "lucide-react";
import { api } from "@/lib/api";
import type { DoctorRecommendation, DoctorRecommendations as Recs } from "@/lib/types";
import { formatKzt } from "@/lib/format";
import { useI18n } from "@/lib/i18n/I18nProvider";

const STYLE: Record<string, { icon: any; chip: string; ring: string }> = {
  bestValue: { icon: Gem, chip: "bg-teal-100 text-teal-700", ring: "ring-teal-300" },
  cheapest: { icon: TrendingDown, chip: "bg-emerald-100 text-emerald-700", ring: "ring-emerald-300" },
  topRated: { icon: Award, chip: "bg-amber-100 text-amber-700", ring: "ring-amber-300" },
  popular: { icon: Flame, chip: "bg-rose-100 text-rose-700", ring: "ring-rose-300" },
  experienced: { icon: Award, chip: "bg-violet-100 text-violet-700", ring: "ring-violet-300" },
};

export function DoctorRecommendations({ region, specialty }: { region: string; specialty: string }) {
  const { t } = useI18n();
  const [recs, setRecs] = useState<Recs | null>(null);

  useEffect(() => {
    if (!region) return;
    api
      .doctorRecommendations({ region, specialty: specialty || undefined })
      .then(setRecs)
      .catch(() => setRecs(null));
  }, [region, specialty]);

  if (!recs || recs.items.length === 0) return null;

  return (
    <div className="rounded-2xl border border-teal-100 bg-gradient-to-br from-teal-50/70 to-brand-50/40 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-white">
          <Sparkles size={17} />
        </span>
        <div>
          <h3 className="font-bold text-ink">{t("rec.title")}</h3>
          <p className="text-xs text-slate-500">{t("rec.subtitle")}</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {recs.items.map((r) => (
          <RecCard key={r.doctor.id} r={r} t={t} />
        ))}
      </div>
    </div>
  );
}

function RecCard({ r, t }: { r: DoctorRecommendation; t: (k: string, v?: any) => string }) {
  const st = STYLE[r.type] || STYLE.bestValue;
  const Icon = st.icon;
  const d = r.doctor;
  const c = d.clinic;
  const price = c?.price_discount || c?.price || d.min_price;
  const rating = r.rating ?? d.rating;

  // localized "reason"
  let reason = "";
  if (r.type === "bestValue") {
    reason = r.below_avg_pct > 0 ? t("rec.belowAvg", { pct: r.below_avg_pct }) : t("rec.topRated");
  } else if (r.type === "cheapest") {
    reason = r.cheaper_than_avg > 0 ? t("rec.cheaperBy", { amount: formatKzt(r.cheaper_than_avg) }) : t("rec.cheapest");
  } else if (r.type === "topRated") {
    reason = rating != null ? t("rec.betterRating", { rating: Number(rating).toFixed(1) }) : t("rec.topRated");
  } else {
    reason = `${r.reviews} ${t("doc.reviews")}`;
  }

  return (
    <Link
      href={`/doctors/${d.id}`}
      className={`card flex flex-col gap-2 p-3 transition hover:-translate-y-0.5 hover:shadow-hover ring-1 ${st.ring}`}
    >
      <span className={`chip self-start ${st.chip}`}><Icon size={12} /> {t(`rec.${r.type}`)}</span>
      <div className="flex items-center gap-2">
        <div className="h-11 w-11 shrink-0 overflow-hidden rounded-xl bg-slate-100">
          {d.avatar && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={d.avatar} alt={d.name} className="h-full w-full object-cover" loading="lazy" />
          )}
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-bold text-ink">{d.name}</div>
          <div className="truncate text-xs text-slate-500">{d.primary_specialty}</div>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-lg font-extrabold text-ink">{price ? formatKzt(price) : "—"}</div>
        {rating != null && (
          <span className="inline-flex items-center gap-0.5 text-sm font-semibold text-amber-600">
            <Star size={13} className="fill-amber-400 text-amber-400" /> {Number(rating).toFixed(2)}
          </span>
        )}
      </div>
      <div className="rounded-lg bg-white/70 px-2 py-1 text-xs font-medium text-teal-700">💡 {reason}</div>
    </Link>
  );
}
