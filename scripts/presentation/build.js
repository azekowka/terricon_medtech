/* Generates the MedServicePrice.kz hackathon deck (7 slides). */
const pptxgen = require("pptxgenjs");
const path = require("path");

const C = {
  dark: "0B132B",
  teal: "0E7C7B",
  seafoam: "00A896",
  mint: "02C39A",
  ink: "12202B",
  muted: "5B6B7A",
  light: "F4F8F8",
  white: "FFFFFF",
  line: "D9E2E2",
};

const HEAD = "Cambria";
const BODY = "Calibri";

const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";
const W = 13.333;
const H = 7.5;

function circle(s, x, y, d, fill, label, lblColor) {
  s.addShape("ellipse", { x, y, w: d, h: d, fill: { color: fill } });
  if (label)
    s.addText(label, {
      x, y, w: d, h: d, align: "center", valign: "middle",
      fontFace: HEAD, fontSize: d * 22, bold: true, color: lblColor || C.white,
    });
}

function footer(s, n) {
  s.addText("MedServicePrice.kz", {
    x: 0.5, y: H - 0.45, w: 4, h: 0.3, fontFace: BODY, fontSize: 9, color: C.muted, align: "left",
  });
  s.addText(`${n} / 7`, {
    x: W - 1.3, y: H - 0.45, w: 0.8, h: 0.3, fontFace: BODY, fontSize: 9, color: C.muted, align: "right",
  });
}

/* ---------- Slide 1: Title (dark) ---------- */
let s = p.addSlide();
s.background = { color: C.dark };
s.addShape("ellipse", { x: 10.4, y: -1.6, w: 4.6, h: 4.6, fill: { color: C.teal } });
s.addShape("ellipse", { x: 11.6, y: 4.6, w: 3.4, h: 3.4, fill: { color: C.seafoam } });
circle(s, 0.9, 0.85, 0.7, C.mint, "+", C.dark);
s.addText("MedServicePrice.kz", {
  x: 1.75, y: 0.85, w: 8, h: 0.7, fontFace: HEAD, fontSize: 26, bold: true, color: C.white, valign: "middle",
});
s.addText("Сравнение цен на медицинские услуги в Казахстане", {
  x: 0.9, y: 2.5, w: 9.6, h: 1.8, fontFace: HEAD, fontSize: 44, bold: true, color: C.white, lineSpacingMultiple: 1.0,
});
s.addText("«Aviasales для медицины»: один поиск вместо десятков сайтов клиник —\nанализы, приёмы врачей и диагностика по лучшей цене рядом с вами.", {
  x: 0.9, y: 4.45, w: 9.4, h: 1.0, fontFace: BODY, fontSize: 16, color: "C9D6D6",
});
const stats = [["911", "цен"], ["22", "клиники"], ["6", "городов"], ["10", "источников"]];
stats.forEach((st, i) => {
  const x = 0.9 + i * 2.35;
  s.addText(st[0], { x, y: 5.75, w: 2.1, h: 0.6, fontFace: HEAD, fontSize: 34, bold: true, color: C.mint });
  s.addText(st[1], { x, y: 6.35, w: 2.1, h: 0.35, fontFace: BODY, fontSize: 13, color: "9FB0B0" });
});
s.addText("Хакатон 2025 · Кейс 1 · Рабочий MVP", {
  x: 0.9, y: 6.95, w: 8, h: 0.35, fontFace: BODY, fontSize: 12, color: "7E9090",
});

/* ---------- Slide 2: Problem / Solution ---------- */
s = p.addSlide();
s.background = { color: C.white };
s.addText("Проблема и решение", {
  x: 0.6, y: 0.45, w: 12, h: 0.7, fontFace: HEAD, fontSize: 34, bold: true, color: C.ink,
});
// problem card
s.addShape("roundRect", { x: 0.6, y: 1.5, w: 5.9, h: 5.2, rectRadius: 0.12, fill: { color: C.light } });
circle(s, 1.0, 1.9, 0.7, "E2574C", "!", C.white);
s.addText("Рынок непрозрачен", { x: 1.9, y: 1.95, w: 4.4, h: 0.6, fontFace: HEAD, fontSize: 20, bold: true, color: C.ink, valign: "middle" });
[
  "Пациент вручную обходит десятки сайтов клиник, чтобы сравнить цену анализа или приёма.",
  "Цены нигде не агрегированы, форматы разные (HTML, PDF, прайсы).",
  "Одна и та же услуга названа по-разному: «ОАК», «CBC», «Клинический анализ крови».",
  "Непонятно, насколько цена актуальна.",
].forEach((t, i) => {
  s.addText(t, { x: 1.0, y: 2.95 + i * 0.92, w: 5.2, h: 0.85, fontFace: BODY, fontSize: 14.5, color: C.muted, bullet: { code: "2022", indent: 14 } });
});
// solution card
s.addShape("roundRect", { x: 6.85, y: 1.5, w: 5.9, h: 5.2, rectRadius: 0.12, fill: { color: C.teal } });
circle(s, 7.25, 1.9, 0.7, C.mint, "✓", C.dark);
s.addText("Единая платформа цен", { x: 8.15, y: 1.95, w: 4.4, h: 0.6, fontFace: HEAD, fontSize: 20, bold: true, color: C.white, valign: "middle" });
[
  "Автосбор прайсов из открытых источников + хранение «сырого» слоя для аудита.",
  "Нормализация названий к единому справочнику услуг (синонимы + нечёткий матч).",
  "Поиск с автодополнением, фильтры, сортировка по цене и расстоянию.",
  "Дата обновления у каждой цены — прозрачность для пациента.",
].forEach((t, i) => {
  s.addText(t, { x: 7.25, y: 2.95 + i * 0.92, w: 5.2, h: 0.85, fontFace: BODY, fontSize: 14.5, color: "EAF4F4", bullet: { code: "2022", indent: 14 } });
});
footer(s, 2);

/* ---------- Slide 3: Architecture ---------- */
s = p.addSlide();
s.background = { color: C.white };
s.addText("Архитектура: три слоя данных", {
  x: 0.6, y: 0.45, w: 12, h: 0.7, fontFace: HEAD, fontSize: 34, bold: true, color: C.ink,
});
const flow = [
  ["Источники", "HTML · PDF\nXLSX · DOCX", C.teal],
  ["RAW-слой", "raw_prices\n(аудит ≥90 дн.)", C.seafoam],
  ["Нормализация", "справочник\n+ rapidfuzz", C.mint],
  ["Prices", "дедуп\n+ история", C.teal],
  ["Веб-интерфейс", "поиск · карта\nсравнение", C.dark],
];
flow.forEach((f, i) => {
  const x = 0.6 + i * 2.55;
  s.addShape("roundRect", { x, y: 2.0, w: 2.2, h: 1.7, rectRadius: 0.1, fill: { color: f[2] } });
  s.addText(f[0], { x, y: 2.2, w: 2.2, h: 0.5, align: "center", fontFace: HEAD, fontSize: 16, bold: true, color: C.white });
  s.addText(f[1], { x, y: 2.75, w: 2.2, h: 0.85, align: "center", fontFace: BODY, fontSize: 12, color: "EAF4F4" });
  if (i < flow.length - 1)
    s.addText("▶", { x: x + 2.18, y: 2.0, w: 0.4, h: 1.7, align: "center", valign: "middle", fontFace: BODY, fontSize: 16, color: C.muted });
});
// callouts under flow
const notes = [
  ["Отказоустойчивость", "падение одного источника не останавливает сбор с остальных"],
  ["Дедупликация", "повторный парсинг обновляет запись, а не плодит дубли"],
  ["Масштабируемость", "новый источник = 1 класс-парсер, ядро не меняется"],
];
notes.forEach((n, i) => {
  const x = 0.6 + i * 4.15;
  s.addShape("roundRect", { x, y: 4.3, w: 3.85, h: 2.0, rectRadius: 0.1, fill: { color: C.light } });
  circle(s, x + 0.25, y0(4.55), 0.55, C.seafoam, String(i + 1));
  s.addText(n[0], { x: x + 0.95, y: 4.6, w: 2.8, h: 0.5, fontFace: HEAD, fontSize: 16, bold: true, color: C.ink, valign: "middle" });
  s.addText(n[1], { x: x + 0.3, y: 5.3, w: 3.3, h: 0.9, fontFace: BODY, fontSize: 13.5, color: C.muted });
});
function y0(v) { return v; }
footer(s, 3);

/* ---------- Slide 4: Normalization (data quality) ---------- */
s = p.addSlide();
s.background = { color: C.dark };
s.addText("Нормализация — ядро качества данных", {
  x: 0.6, y: 0.45, w: 12, h: 0.7, fontFace: HEAD, fontSize: 32, bold: true, color: C.white,
});
// synonyms -> one service
const syn = ["«ОАК»", "«CBC»", "«Клинический анализ крови»", "«Общий анализ крови с лейкоформулой»"];
syn.forEach((t, i) => {
  s.addShape("roundRect", { x: 0.7, y: 1.7 + i * 0.78, w: 4.5, h: 0.6, rectRadius: 0.3, fill: { color: "1C2A45" } });
  s.addText(t, { x: 0.9, y: 1.7 + i * 0.78, w: 4.1, h: 0.6, fontFace: BODY, fontSize: 14, color: "CFE7E5", valign: "middle" });
});
s.addText("▶", { x: 5.35, y: 2.4, w: 0.8, h: 1.4, align: "center", valign: "middle", fontFace: BODY, fontSize: 26, color: C.mint });
s.addShape("roundRect", { x: 6.3, y: 2.25, w: 6.3, h: 1.5, rectRadius: 0.12, fill: { color: C.mint } });
s.addText("Общий анализ крови (ОАК)", { x: 6.5, y: 2.4, w: 5.9, h: 0.7, fontFace: HEAD, fontSize: 21, bold: true, color: C.dark });
s.addText("одна каноническая услуга · категория: Лаборатория", { x: 6.5, y: 3.05, w: 5.9, h: 0.5, fontFace: BODY, fontSize: 13, color: "0B3B38" });
// stat callouts
const k = [["99%", "названий привязано\nавтоматически"], ["exact + fuzzy", "точное совпадение\n→ rapidfuzz ≥ 86"], ["unmatched", "очередь ручной\nразметки + дообучение"]];
k.forEach((c, i) => {
  const x = 0.7 + i * 4.1;
  s.addText(c[0], { x, y: 4.55, w: 3.8, h: 0.8, fontFace: HEAD, fontSize: 30, bold: true, color: C.mint });
  s.addText(c[1], { x, y: 5.4, w: 3.8, h: 0.9, fontFace: BODY, fontSize: 14, color: "AFC4C4" });
});
footer(s, 4);

/* ---------- Slide 5: Features ---------- */
s = p.addSlide();
s.background = { color: C.white };
s.addText("Возможности интерфейса", {
  x: 0.6, y: 0.45, w: 12, h: 0.7, fontFace: HEAD, fontSize: 34, bold: true, color: C.ink,
});
const feats = [
  ["Поиск + автодополнение", "по справочнику, понимает синонимы и сокращения"],
  ["Фильтры и сортировки", "город, категория, цена, рейтинг, онлайн-запись, расстояние"],
  ["Сравнение клиник", "таблица предложений с выделением лучшей цены"],
  ["История изменения цен", "график динамики по каждой клинике"],
  ["Карта клиник", "Leaflet-маркеры + маршрут в 2GIS"],
  ["Подписка на цену", "уведомление при снижении до целевой"],
];
feats.forEach((f, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.6 + col * 6.25, y = 1.55 + row * 1.75;
  s.addShape("roundRect", { x, y, w: 5.95, h: 1.55, rectRadius: 0.1, fill: { color: C.light } });
  circle(s, x + 0.3, y + 0.45, 0.65, i % 2 ? C.seafoam : C.teal, String(i + 1));
  s.addText(f[0], { x: x + 1.15, y: y + 0.25, w: 4.6, h: 0.5, fontFace: HEAD, fontSize: 17, bold: true, color: C.ink });
  s.addText(f[1], { x: x + 1.15, y: y + 0.78, w: 4.65, h: 0.65, fontFace: BODY, fontSize: 13, color: C.muted });
});
footer(s, 5);

/* ---------- Slide 6: Data & stack ---------- */
s = p.addSlide();
s.background = { color: C.white };
s.addText("Данные, охват и стек", {
  x: 0.6, y: 0.45, w: 12, h: 0.7, fontFace: HEAD, fontSize: 34, bold: true, color: C.ink,
});
const big = [["911", "актуальных цен"], ["22", "клиники"], ["6", "городов"], ["69", "услуг"], ["10", "источников"], ["99%", "нормализовано"]];
big.forEach((b, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.6 + col * 4.15, y = 1.5 + row * 1.45;
  s.addShape("roundRect", { x, y, w: 3.85, h: 1.25, rectRadius: 0.1, fill: { color: i % 2 ? C.teal : C.seafoam } });
  s.addText(b[0], { x: x + 0.2, y: y + 0.12, w: 3.5, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, color: C.white });
  s.addText(b[1], { x: x + 0.2, y: y + 0.78, w: 3.5, h: 0.4, fontFace: BODY, fontSize: 13, color: "EAF4F4" });
});
s.addText("Технологический стек", { x: 0.6, y: 4.65, w: 8, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: C.ink });
const stack = [
  "Парсинг: Python · httpx · BeautifulSoup · pdfplumber · openpyxl · rapidfuzz (HTML/PDF/XLSX/DOCX)",
  "Backend: FastAPI · SQLAlchemy 2.0 · APScheduler",
  "БД: PostgreSQL (prod) / SQLite (dev)",
  "Frontend: Next.js 14 · TypeScript · Tailwind · Leaflet · Recharts",
  "Деплой: Docker · docker-compose",
];
stack.forEach((t, i) => {
  s.addText(t, { x: 0.7, y: 5.2 + i * 0.4, w: 12, h: 0.4, fontFace: BODY, fontSize: 14, color: C.muted, bullet: { code: "25AA", indent: 14 } });
});
footer(s, 6);

/* ---------- Slide 7: Roadmap / closing (dark) ---------- */
s = p.addSlide();
s.background = { color: C.dark };
s.addShape("ellipse", { x: -1.5, y: 4.8, w: 4.4, h: 4.4, fill: { color: C.teal } });
s.addShape("ellipse", { x: 11.5, y: -1.4, w: 3.6, h: 3.6, fill: { color: C.seafoam } });
s.addText("План развития", {
  x: 0.7, y: 0.7, w: 11, h: 0.8, fontFace: HEAD, fontSize: 36, bold: true, color: C.white,
});
const road = [
  ["Больше источников", "PDF/DOCX/Excel-прайсы, расширение городов и регионов РК"],
  ["AI-нормализация", "LLM-сопоставление сложных «чек-апов» и комплексов услуг"],
  ["Геопоиск и запись", "интеграция с 2GIS/картами, онлайн-запись в клиники"],
  ["Уведомления", "e-mail/Telegram-алерты о снижении цены, дашборд трендов"],
];
road.forEach((r, i) => {
  const y = 1.9 + i * 1.12;
  circle(s, 0.8, y, 0.7, C.mint, String(i + 1), C.dark);
  s.addText(r[0], { x: 1.75, y: y - 0.05, w: 4.0, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: C.white });
  s.addText(r[1], { x: 1.75, y: y + 0.42, w: 10.5, h: 0.5, fontFace: BODY, fontSize: 14, color: "AFC4C4" });
});
s.addText("Спасибо! · MedServicePrice.kz", {
  x: 0.7, y: 6.5, w: 11, h: 0.6, fontFace: HEAD, fontSize: 20, bold: true, color: C.mint,
});

const out = path.join(__dirname, "..", "..", "docs", "MedServicePrice_Presentation.pptx");
p.writeFile({ fileName: out }).then(() => console.log("Wrote", out));
