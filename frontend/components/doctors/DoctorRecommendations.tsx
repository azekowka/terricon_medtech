"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, Star, TrendingDown, Award, Flame, Gem, Lightbulb } from "lucide-react";
import { api } from "@/lib/api";
import type { DoctorRecommendation, DoctorRecommendations as Recs } from "@/lib/types";
import { formatKzt } from "@/lib/format";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { DoctorAvatar } from "@/components/DoctorAvatar";

const STYLE: Record<string, { icon: any; chip: string }> = {
  bestValue: { icon: Gem, chip: "bg-teal-50 text-teal-700" },
  cheapest: { icon: TrendingDown, chip: "bg-emerald-50 text-emerald-700" },
  topRated: { icon: Award, chip: "bg-amber-50 text-amber-700" },
  popular: { icon: Flame, chip: "bg-slate-100 text-slate-600" },
  experienced: { icon: Award, chip: "bg-violet-50 text-violet-700" },
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
    <div className="rounded-2xl border border-teal-100 bg-teal-50/50 p-4">
      <div className="mb-3 flex items-center gap-2.5">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-100 text-teal-700">
          <Sparkles size={18} strokeWidth={1.75} />
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
      className="card flex flex-col gap-2 p-3 transition duration-200 hover:-translate-y-0.5 hover:shadow-hover"
    >
      <span className={`chip self-start ${st.chip}`}><Icon size={12} strokeWidth={1.75} /> {t(`rec.${r.type}`)}</span>
      <div className="flex items-center gap-2">
        <DoctorAvatar src={d.avatar} name={d.name} className="h-11 w-11 shrink-0 rounded-xl" iconSize={18} />
        <div className="min-w-0">
          <div className="truncate text-sm font-bold text-ink">{d.name}</div>
          <div className="truncate text-xs text-slate-500">{d.primary_specialty}</div>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-lg font-bold tracking-tight text-ink">{price ? formatKzt(price) : "—"}</div>
        {rating != null && (
          <span className="inline-flex items-center gap-0.5 text-sm font-semibold text-amber-600">
            <Star size={13} className="fill-amber-400 text-amber-400" /> {Number(rating).toFixed(2)}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600">
        <Lightbulb size={13} strokeWidth={1.75} className="shrink-0 text-teal-600" /> {reason}
      </div>
    </Link>
  );
}
