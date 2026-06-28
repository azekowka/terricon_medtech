"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Database, Loader2, Play, RefreshCw, Tags } from "lucide-react";
import { api } from "@/lib/api";
import type { ServiceItem } from "@/lib/types";

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [unmatched, setUnmatched] = useState<any[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState<any>(null);

  async function refresh() {
    const [s, l, u, sv] = await Promise.all([
      api.stats(),
      api.parseLogs(),
      api.unmatched(),
      api.services({ limit: 2000 }),
    ]);
    setStats(s);
    setLogs(l);
    setUnmatched(u);
    setServices(sv);
  }

  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  async function runParse(includeLive: boolean) {
    setRunning(true);
    setLastRun(null);
    try {
      const res = await api.triggerParse({ sources: ["seed"], include_live: includeLive });
      setLastRun(res);
      await refresh();
    } finally {
      setRunning(false);
    }
  }

  async function resolve(id: string, serviceId: string) {
    if (!serviceId) return;
    await api.resolveUnmatched(id, { service_id: serviceId, add_synonym: true });
    await refresh();
  }

  return (
    <div className="container-page pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Панель администратора</h1>
          <p className="mt-1 text-sm text-slate-500">Сбор данных, журнал парсинга и нормализация справочника</p>
        </div>
        <button onClick={() => refresh()} className="btn-outline">
          <RefreshCw size={16} /> Обновить
        </button>
      </div>

      {/* Stats */}
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Клиники" value={stats?.clinics} />
        <StatCard label="Услуги (справочник)" value={stats?.services} />
        <StatCard label="Активные цены" value={stats?.active_prices} />
        <StatCard label="Привязано" value={stats?.matched_prices} accent="emerald" />
        <StatCard label="В очереди разметки" value={stats?.unmatched_pending} accent="amber" />
        <StatCard label="Raw-слой (аудит)" value={stats?.raw_rows} />
      </div>

      {/* Parse controls */}
      <div className="card mt-6 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
            <Database size={18} strokeWidth={1.75} />
          </span>
          <span className="font-bold text-ink">Запуск парсинга</span>
          <div className="ml-auto flex gap-2">
            <button onClick={() => runParse(false)} disabled={running} className="btn-primary">
              {running ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />} Seed-источник
            </button>
            <button onClick={() => runParse(true)} disabled={running} className="btn-outline">
              + Live-источники (web)
            </button>
          </div>
        </div>
        {lastRun && (
          <div className="mt-4 space-y-1 rounded-xl bg-slate-50 p-3 text-sm">
            {lastRun.runs.map((r: any) => (
              <div key={r.id} className="flex items-center justify-between">
                <span className="font-medium text-ink">
                  {r.source}{" "}
                  <span className={`chip ${r.status === "success" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                    {r.status}
                  </span>
                </span>
                <span className="text-slate-500">
                  найдено {r.records_found} · новых {r.records_new} · обновлено {r.records_updated} · ошибок {r.errors_count}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Unmatched queue */}
        <div className="card p-5">
          <div className="mb-3 flex items-center gap-2.5 font-bold text-ink">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <Tags size={18} strokeWidth={1.75} />
            </span>
            Очередь ручной разметки
            <span className="chip bg-amber-50 text-amber-700">{unmatched.length}</span>
          </div>
          {unmatched.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                <CheckCircle2 size={20} strokeWidth={1.75} />
              </span>
              <p className="text-sm text-slate-500">Очередь пуста</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {unmatched.map((u) => (
                <li key={u.id} className="rounded-xl border border-slate-200 p-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="font-medium text-ink">{u.service_name_raw}</div>
                      <div className="mt-0.5 text-xs text-slate-500">
                        {u.source} · встречается {u.occurrences}×
                        {u.suggested_service_name && ` · похоже на «${u.suggested_service_name}» (${Math.round(u.suggested_score)}%)`}
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <select
                      className="input py-1.5 text-sm"
                      defaultValue={u.suggested_service_id || ""}
                      id={`sel-${u.id}`}
                    >
                      <option value="">— выбрать услугу —</option>
                      {services.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() =>
                        resolve(u.id, (document.getElementById(`sel-${u.id}`) as HTMLSelectElement).value)
                      }
                      className="btn-primary py-1.5"
                    >
                      Привязать
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Parse logs */}
        <div className="card p-5">
          <div className="mb-3 font-bold text-ink">Журнал парсинга</div>
          <div className="max-h-[420px] space-y-2 overflow-y-auto">
            {logs.map((l) => (
              <div key={l.id} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm">
                <span className="font-medium text-ink">
                  {l.source}{" "}
                  <span
                    className={`chip ${
                      l.status === "success"
                        ? "bg-emerald-50 text-emerald-700"
                        : l.status === "error"
                        ? "bg-red-50 text-red-700"
                        : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    {l.status}
                  </span>
                </span>
                <span className="text-xs text-slate-500">
                  {l.records_found} зап. · {l.errors_count} ош. · {new Date(l.started_at).toLocaleString("ru-RU")}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Distribution */}
      {stats && (
        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          <DistCard title="Цены по источникам" data={stats.prices_by_source} />
          <DistCard title="Цены по категориям" data={stats.prices_by_category} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: number | undefined; accent?: string }) {
  const color = accent === "emerald" ? "text-emerald-600" : accent === "amber" ? "text-amber-600" : "text-ink";
  return (
    <div className="card p-4">
      <div className={`text-2xl font-bold tracking-tight ${color}`}>{value ?? "—"}</div>
      <div className="mt-0.5 text-xs text-slate-500">{label}</div>
    </div>
  );
}

function DistCard({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data || {}).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map((e) => e[1]));
  return (
    <div className="card p-5">
      <div className="mb-3 font-bold text-ink">{title}</div>
      <div className="space-y-2">
        {entries.map(([k, v]) => (
          <div key={k}>
            <div className="mb-0.5 flex justify-between text-xs text-slate-500">
              <span>{k || "—"}</span>
              <span className="font-medium text-ink">{v}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-brand-500" style={{ width: `${(v / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
