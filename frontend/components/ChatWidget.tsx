"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bot, MessageCircle, Send, Sparkles, X } from "lucide-react";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n/I18nProvider";

interface Action {
  label: string;
  href: string;
}
interface Msg {
  role: "user" | "bot";
  text: string;
  actions?: Action[];
}

export function ChatWidget() {
  const { t, locale } = useI18n();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // seed greeting on first open
  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{ role: "bot", text: t("chat.greeting") }]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || loading) return;
    const history = messages.map((m) => ({ role: m.role, text: m.text }));
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await api.assistantChat(q, locale, history);
      setMessages((m) => [...m, { role: "bot", text: res.reply, actions: res.actions }]);
    } catch {
      setMessages((m) => [...m, { role: "bot", text: t("chat.error") }]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  const suggestions = [t("chat.s1"), t("chat.s2"), t("chat.s3")];

  return (
    <>
      {/* launcher */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          aria-label="chat"
          className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-white shadow-hover transition hover:scale-105 hover:bg-brand-700"
        >
          <MessageCircle size={26} />
          <span className="absolute right-0.5 top-0.5 h-3 w-3 rounded-full border-2 border-white bg-teal-400" />
        </button>
      )}

      {/* panel */}
      {open && (
        <div className="fixed bottom-5 right-5 z-50 flex h-[560px] max-h-[85vh] w-[380px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-pop">
          {/* header */}
          <div className="flex items-center justify-between bg-brand-600 px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
                <Bot size={20} strokeWidth={1.75} />
              </span>
              <div>
                <div className="text-sm font-bold leading-tight">{t("chat.title")}</div>
                <div className="text-xs text-brand-50">{t("chat.subtitle")}</div>
              </div>
            </div>
            <button onClick={() => setOpen(false)} className="rounded-lg p-1 transition hover:bg-white/15" aria-label="close">
              <X size={20} />
            </button>
          </div>

          {/* messages */}
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-3">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] ${m.role === "user" ? "" : "flex gap-2"}`}>
                  {m.role === "bot" && (
                    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                      <Bot size={15} />
                    </span>
                  )}
                  <div>
                    <div
                      className={`whitespace-pre-line rounded-2xl px-3.5 py-2.5 text-sm ${
                        m.role === "user"
                          ? "rounded-br-md bg-brand-600 text-white"
                          : "rounded-bl-md bg-white text-slate-700 shadow-card"
                      }`}
                    >
                      {m.text}
                    </div>
                    {m.actions && m.actions.length > 0 && (
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {m.actions.map((a, j) => (
                          <Link
                            key={j}
                            href={a.href}
                            onClick={() => setOpen(false)}
                            className="chip bg-brand-50 text-brand-700 hover:bg-brand-100"
                          >
                            {a.label} →
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="flex gap-2">
                  <span className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                    <Bot size={15} />
                  </span>
                  <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-white px-4 py-3 shadow-card">
                    {[0, 150, 300].map((d) => (
                      <span
                        key={d}
                        className="h-2 w-2 animate-bounce rounded-full bg-slate-300"
                        style={{ animationDelay: `${d}ms` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* suggestions (only at the start) */}
            {messages.length <= 1 && !loading && (
              <div className="flex flex-col items-start gap-1.5 pt-1">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="flex items-center gap-1.5 rounded-full border border-brand-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-50"
                  >
                    <Sparkles size={12} /> {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* input */}
          <div className="flex items-end gap-2 border-t border-slate-100 bg-white p-2.5">
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder={t("chat.placeholder")}
              className="max-h-24 flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15"
            />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition hover:bg-brand-700 disabled:opacity-40"
              aria-label={t("chat.send")}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
