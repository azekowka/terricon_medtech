"use client";

import Link from "next/link";
import { BadgeCheck, CalendarCheck, MapPin, Star } from "lucide-react";
import type { DoctorCard as Doctor } from "@/lib/types";
import { formatKzt, yearsLabel } from "@/lib/format";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { DoctorAvatar } from "@/components/DoctorAvatar";

export function DoctorCard({ doctor }: { doctor: Doctor; onBook?: () => void }) {
  const { t, locale } = useI18n();
  const href = `/doctors/${doctor.id}`;
  const patientLabel = doctor.accepts_children ? t("doc.acceptsKids") : t("doc.acceptsAdults");
  const c = doctor.clinic;
  const specs = doctor.specialties?.map((s) => s.name) || [];
  const specLabel = doctor.primary_specialty || specs[0] || "Врач";
  const extra = specs.length > 1 ? specs.slice(1, 3) : [];
  return (
    <div className="card flex flex-col gap-4 p-4 transition hover:shadow-hover sm:flex-row sm:p-5">
      {/* avatar */}
      <Link href={href} className="relative shrink-0">
        <DoctorAvatar src={doctor.avatar} name={doctor.name} className="h-24 w-24 rounded-2xl" iconSize={34} />
        {doctor.verified && (
          <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-white text-brand-600 shadow">
            <BadgeCheck size={20} className="fill-brand-100" />
          </span>
        )}
      </Link>

      {/* info */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          {doctor.top && <span className="chip bg-amber-100 text-amber-700">ТОП</span>}
          <Link href={href} className="text-lg font-bold leading-tight text-ink hover:text-brand-700">
            {doctor.name}
          </Link>
        </div>
        <p className="mt-0.5 font-medium text-brand-700">{specLabel}</p>
        {extra.length > 0 && (
          <p className="text-sm text-slate-400">{extra.join(" · ")}{specs.length > 3 ? " …" : ""}</p>
        )}

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
          {doctor.experience_years != null && (
            <span>{t("doc.experience")} {doctor.experience_years} {yearsLabel(doctor.experience_years, locale)}</span>
          )}
          {doctor.category && <span className="text-slate-400">• {doctor.category}</span>}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <span className="chip bg-emerald-50 text-emerald-700">{patientLabel}</span>
          {doctor.rating != null && (
            <span className="chip bg-amber-50 text-amber-700">
              <Star size={12} className="fill-amber-400 text-amber-400" /> {doctor.rating.toFixed(2)}
            </span>
          )}
          {doctor.reviews > 0 && (
            <span className="text-xs text-slate-400">
              {doctor.reviews} {t("doc.reviews")}
            </span>
          )}
        </div>

        {c && (
          <div className="mt-2.5 border-t border-slate-100 pt-2.5 text-sm">
            <div className="font-semibold text-ink">{c.name}</div>
            {c.address && (
              <div className="flex items-center gap-1 text-slate-500">
                <MapPin size={13} /> {c.address}
              </div>
            )}
            {doctor.clinics_count > 1 && (
              <div className="mt-0.5 text-xs font-medium text-brand-600">
                {t("doc.moreClinics", { n: doctor.clinics_count - 1 })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* price + book */}
      <div className="flex shrink-0 flex-col items-stretch justify-center gap-2 border-t border-slate-100 pt-3 sm:w-44 sm:border-l sm:border-t-0 sm:pl-4 sm:pt-0">
        {c?.online_booking && (
          <span className="chip self-start bg-emerald-50 text-emerald-700">
            <CalendarCheck size={12} /> {t("doc.online")}
          </span>
        )}
        <div className="text-right sm:text-left">
          {c?.discount ? (
            <>
              <div className="text-sm text-slate-400 line-through">{formatKzt(c.price)}</div>
              <div className="text-2xl font-extrabold text-ink">{formatKzt(c.price_discount)}</div>
              <span className="chip mt-1 bg-teal-100 text-teal-700">-{c.discount}% {t("doc.discount")}</span>
            </>
          ) : (
            <div className="text-2xl font-extrabold text-ink">
              {c?.price ? formatKzt(c.price) : doctor.min_price ? formatKzt(doctor.min_price) : "—"}
            </div>
          )}
        </div>
        <Link href={href} className="btn-primary w-full">
          {t("common.book")}
        </Link>
      </div>
    </div>
  );
}
