"use client";

import { BadgeCheck, CalendarCheck, MapPin, Star, Stethoscope } from "lucide-react";
import type { DoctorCard as Doctor } from "@/lib/types";
import { formatKzt, pluralRu } from "@/lib/format";

function patientLabel(d: Doctor): string {
  if (d.accepts_children) return "Принимает детей и взрослых";
  return "Принимает взрослых";
}

export function DoctorCard({ doctor, onBook }: { doctor: Doctor; onBook: () => void }) {
  const c = doctor.clinic;
  const specs = doctor.specialties?.map((s) => s.name) || [];
  const specLabel = doctor.primary_specialty || specs[0] || "Врач";
  const extra = specs.length > 1 ? specs.slice(1, 3) : [];
  return (
    <div className="card flex flex-col gap-4 p-4 transition hover:shadow-hover sm:flex-row sm:p-5">
      {/* avatar */}
      <div className="relative shrink-0">
        <div className="h-24 w-24 overflow-hidden rounded-2xl bg-slate-100">
          {doctor.avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={doctor.avatar} alt={doctor.name} className="h-full w-full object-cover" loading="lazy" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-slate-300">
              <Stethoscope size={34} />
            </div>
          )}
        </div>
        {doctor.verified && (
          <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-white text-brand-600 shadow">
            <BadgeCheck size={20} className="fill-brand-100" />
          </span>
        )}
      </div>

      {/* info */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          {doctor.top && <span className="chip bg-amber-100 text-amber-700">ТОП</span>}
          <h3 className="text-lg font-bold leading-tight text-ink">{doctor.name}</h3>
        </div>
        <p className="mt-0.5 font-medium text-brand-700">{specLabel}</p>
        {extra.length > 0 && (
          <p className="text-sm text-slate-400">{extra.join(" · ")}{specs.length > 3 ? " …" : ""}</p>
        )}

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
          {doctor.experience_years != null && (
            <span>Стаж {doctor.experience_years} {pluralRu(doctor.experience_years, ["год", "года", "лет"])}</span>
          )}
          {doctor.category && <span className="text-slate-400">• {doctor.category}</span>}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <span className="chip bg-emerald-50 text-emerald-700">{patientLabel(doctor)}</span>
          {doctor.rating != null && (
            <span className="chip bg-amber-50 text-amber-700">
              <Star size={12} className="fill-amber-400 text-amber-400" /> {doctor.rating.toFixed(2)}
            </span>
          )}
          {doctor.reviews > 0 && (
            <span className="text-xs text-slate-400">
              {doctor.reviews} {pluralRu(doctor.reviews, ["отзыв", "отзыва", "отзывов"])}
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
                и ещё {doctor.clinics_count - 1} {pluralRu(doctor.clinics_count - 1, ["клиника", "клиники", "клиник"])}
              </div>
            )}
          </div>
        )}
      </div>

      {/* price + book */}
      <div className="flex shrink-0 flex-col items-stretch justify-center gap-2 border-t border-slate-100 pt-3 sm:w-44 sm:border-l sm:border-t-0 sm:pl-4 sm:pt-0">
        {c?.online_booking && (
          <span className="chip self-start bg-emerald-50 text-emerald-700">
            <CalendarCheck size={12} /> Онлайн-запись
          </span>
        )}
        <div className="text-right sm:text-left">
          {c?.discount ? (
            <>
              <div className="text-sm text-slate-400 line-through">{formatKzt(c.price)}</div>
              <div className="text-2xl font-extrabold text-ink">{formatKzt(c.price_discount)}</div>
              <span className="chip mt-1 bg-teal-100 text-teal-700">-{c.discount}% от MedService</span>
            </>
          ) : (
            <div className="text-2xl font-extrabold text-ink">
              {c?.price ? formatKzt(c.price) : doctor.min_price ? formatKzt(doctor.min_price) : "—"}
            </div>
          )}
        </div>
        <button onClick={onBook} className="btn-primary w-full">
          Записаться
        </button>
      </div>
    </div>
  );
}
