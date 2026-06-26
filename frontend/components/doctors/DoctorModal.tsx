"use client";

import { useEffect, useState } from "react";
import { BadgeCheck, CalendarCheck, Check, Clock, ExternalLink, MapPin, Star, X } from "lucide-react";
import { api } from "@/lib/api";
import type { DoctorCard, DoctorDetail } from "@/lib/types";
import { formatKzt, pluralRu } from "@/lib/format";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function DoctorModal({ doctor, onClose }: { doctor: DoctorCard; onClose: () => void }) {
  const [detail, setDetail] = useState<DoctorDetail | null>(null);
  const [booked, setBooked] = useState(false);

  useEffect(() => {
    api.doctor(doctor.id).then(setDetail).catch(() => {});
  }, [doctor.id]);

  const d = detail;
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/40 p-4 py-10" onClick={onClose}>
      <div className="card w-full max-w-2xl p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div className="flex gap-4">
            <div className="h-20 w-20 overflow-hidden rounded-2xl bg-slate-100">
              {doctor.avatar && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={doctor.avatar} alt={doctor.name} className="h-full w-full object-cover" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-ink">{doctor.name}</h2>
                {doctor.verified && <BadgeCheck size={18} className="text-brand-600" />}
              </div>
              <p className="font-medium text-brand-700">{doctor.primary_specialty}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                {doctor.experience_years != null && (
                  <span>Стаж {doctor.experience_years} {pluralRu(doctor.experience_years, ["год", "года", "лет"])}</span>
                )}
                {doctor.category && <span>• {doctor.category}</span>}
                {doctor.rating != null && (
                  <span className="inline-flex items-center gap-1 text-amber-600">
                    <Star size={13} className="fill-amber-400 text-amber-400" /> {doctor.rating.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X size={22} />
          </button>
        </div>

        {/* specialties */}
        {doctor.specialties?.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {doctor.specialties.map((s) => (
              <span key={s.alias} className="chip bg-brand-50 text-brand-700">{s.name}</span>
            ))}
          </div>
        )}

        {/* diseases */}
        {d?.diseases && d.diseases.length > 0 && (
          <div className="mt-4">
            <h3 className="mb-1.5 text-sm font-bold text-ink">Лечение заболеваний</h3>
            <div className="flex flex-wrap gap-1.5">
              {d.diseases.map((dis) => (
                <span key={dis} className="chip bg-slate-100 text-slate-600">{dis}</span>
              ))}
            </div>
          </div>
        )}

        {/* clinics with schedule */}
        <div className="mt-4 space-y-3">
          <h3 className="text-sm font-bold text-ink">
            Где принимает {d ? `(${d.clinics.length})` : ""}
          </h3>
          {(d?.clinics || (doctor.clinic ? [doctor.clinic] : [])).map((c, i) => (
            <div key={i} className="rounded-xl border border-slate-100 p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-semibold text-ink">{c.name}</div>
                  {c.address && (
                    <div className="flex items-center gap-1 text-sm text-slate-500">
                      <MapPin size={13} /> {c.address}
                    </div>
                  )}
                </div>
                <div className="shrink-0 text-right">
                  {c.discount ? (
                    <>
                      <div className="text-xs text-slate-400 line-through">{formatKzt(c.price)}</div>
                      <div className="font-bold text-ink">{formatKzt(c.price_discount)}</div>
                    </>
                  ) : (
                    <div className="font-bold text-ink">{c.price ? formatKzt(c.price) : "—"}</div>
                  )}
                </div>
              </div>
              {c.online_booking && (
                <span className="chip mt-1.5 bg-emerald-50 text-emerald-700">
                  <CalendarCheck size={12} /> Онлайн-запись
                </span>
              )}
              {c.schedule && c.schedule.some((s) => s.work) && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
                  <Clock size={13} className="shrink-0 text-slate-400" />
                  <div className="flex flex-wrap gap-1.5">
                    {c.schedule.map((s, j) => (
                      <span
                        key={j}
                        className={`rounded px-1.5 py-0.5 ${s.work ? "bg-emerald-50 text-emerald-700" : "bg-slate-50 text-slate-300"}`}
                      >
                        {DAYS[j] || s.day}{s.work ? ` ${s.h24 ? "круглосут." : `${s.start}–${s.end}`}` : " —"}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* booking */}
        <div className="mt-5 flex items-center justify-between gap-3 border-t border-slate-100 pt-4">
          {d?.profile_url && (
            <a href={d.profile_url} target="_blank" rel="noopener noreferrer" className="btn-outline">
              Профиль <ExternalLink size={14} />
            </a>
          )}
          {booked ? (
            <span className="inline-flex items-center gap-2 font-semibold text-emerald-600">
              <Check size={18} /> Заявка отправлена!
            </span>
          ) : (
            <button onClick={() => setBooked(true)} className="btn-primary">
              Записаться на приём
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
