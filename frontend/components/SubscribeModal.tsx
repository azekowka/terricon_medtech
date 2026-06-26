"use client";

import { useState } from "react";
import { Bell, X, Check } from "lucide-react";
import { api } from "@/lib/api";
import { formatKzt } from "@/lib/format";

export function SubscribeModal({
  serviceId,
  serviceName,
  clinic,
  onClose,
}: {
  serviceId: string;
  serviceName: string;
  clinic?: { id: string; name: string; price: number } | null;
  onClose: () => void;
}) {
  const [email, setEmail] = useState("");
  const [target, setTarget] = useState(clinic ? String(clinic.price) : "");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!email.includes("@")) {
      setError("Введите корректный e-mail");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.subscribe({
        email,
        service_id: serviceId,
        clinic_id: clinic?.id,
        target_price_kzt: target ? Number(target) : undefined,
      });
      setDone(true);
    } catch {
      setError("Не удалось оформить подписку");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4" onClick={onClose}>
      <div className="card w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-lg font-bold text-ink">
            <Bell size={20} className="text-brand-600" /> Подписка на цену
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X size={20} />
          </button>
        </div>

        {done ? (
          <div className="mt-6 flex flex-col items-center gap-3 py-6 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <Check size={28} />
            </span>
            <p className="font-semibold text-ink">Готово! Мы пришлём письмо при снижении цены.</p>
            <button onClick={onClose} className="btn-primary mt-2">
              Закрыть
            </button>
          </div>
        ) : (
          <>
            <p className="mt-2 text-sm text-slate-500">
              Услуга: <b className="text-ink">{serviceName}</b>
              {clinic && (
                <>
                  {" "}· {clinic.name} ({formatKzt(clinic.price)})
                </>
              )}
            </p>
            <div className="mt-4 space-y-3">
              <div>
                <label className="label">E-mail</label>
                <input
                  className="input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <label className="label">Уведомить, если цена ниже (₸), необязательно</label>
                <input
                  type="number"
                  className="input"
                  placeholder="например, 2000"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button onClick={submit} disabled={loading} className="btn-primary w-full">
                {loading ? "Оформляем…" : "Подписаться"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
