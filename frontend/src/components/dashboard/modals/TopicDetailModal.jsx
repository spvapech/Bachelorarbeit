import * as React from "react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import {
  ChevronLeft, ChevronRight, ArrowLeft, AlertTriangle, Eye, EyeOff,
  MessageSquare, Hash, Star as StarIcon, BarChart3, Quote, Settings2,
} from "lucide-react"
import {
  AreaChart, Area, ComposedChart, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"
import { DropdownPicker } from "../ChartHeader"
import { Tag } from "../../../icons"
import ReviewDetailModal from "./ReviewDetailModal"

/* ─────────── Helpers ─────────── */
const fmt = (n, d = 1) =>
  Number.isFinite(Number(n)) ? Number(n).toFixed(d).replace(".", ",") : "—"

const ratingTone = (s) => {
  const n = Number(s)
  if (!Number.isFinite(n)) return {
    text: "text-slate-700", bar: "bg-slate-300", bg: "bg-slate-50",
    border: "border-slate-200", hex: "#94a3b8", label: "Keine Daten",
  }
  if (n >= 3.5) return {
    text: "text-emerald-700", bar: "bg-emerald-500", bg: "bg-emerald-50",
    border: "border-emerald-200", hex: "#10b981", label: "Gut",
  }
  if (n >= 2.5) return {
    text: "text-amber-700", bar: "bg-amber-500", bg: "bg-amber-50",
    border: "border-amber-200", hex: "#f59e0b", label: "Mittel",
  }
  return {
    text: "text-rose-700", bar: "bg-rose-500", bg: "bg-rose-50",
    border: "border-rose-200", hex: "#f43f5e", label: "Kritisch",
  }
}

const sentimentMeta = (sentiment) => {
  const s = String(sentiment || "").toLowerCase()
  if (s.includes("pos")) return { tone: "good", label: "Positiv", color: "#10b981", text: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500", value: 0.7,  accent: "bg-emerald-500" }
  if (s.includes("neg")) return { tone: "bad",  label: "Negativ", color: "#f43f5e", text: "text-rose-700",    bg: "bg-rose-50",    border: "border-rose-200",    dot: "bg-rose-500",    value: -0.7, accent: "bg-rose-500" }
  if (s.includes("neu")) return { tone: "warn", label: "Neutral", color: "#94a3b8", text: "text-slate-600",   bg: "bg-slate-100",  border: "border-slate-300",   dot: "bg-slate-400",   value: 0.0,  accent: "bg-slate-500" }
  return { tone: "neutral", label: sentiment || "—", color: "#94a3b8", text: "text-slate-600", bg: "bg-slate-50", border: "border-slate-200", dot: "bg-slate-400", value: 0.0, accent: "bg-slate-500" }
}

/* Fill gaps in monthly time series → returns { data, hasGaps } */
function processTimelineDataWithGaps(data) {
  if (!data || data.length < 2) return { data: data || [], hasGaps: false }
  const validData = data.filter((d) => d.year && d.monthNum)
  if (validData.length < 2) return { data: data || [], hasGaps: false }

  const sorted = [...validData].sort((a, b) =>
    a.year !== b.year ? a.year - b.year : a.monthNum - b.monthNum
  )
  const dataMap = new Map(sorted.map((it) => [`${it.year}-${it.monthNum}`, it]))
  const months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

  const result = []
  let hasGaps = false
  let y = sorted[0].year, m = sorted[0].monthNum
  const last = sorted[sorted.length - 1]
  while (y < last.year || (y === last.year && m <= last.monthNum)) {
    const ex = dataMap.get(`${y}-${m}`)
    if (ex) result.push({ ...ex, ratingGap: null })
    else {
      hasGaps = true
      result.push({ month: `${months[m - 1]} ${y}`, year: y, monthNum: m, rating: null, ratingGap: null, _isMissing: true })
    }
    m += 1
    if (m > 12) { m = 1; y += 1 }
  }

  // Interpolate gap segments
  let i = 0
  while (i < result.length) {
    if (!result[i]._isMissing) { i++; continue }
    const start = i
    let end = i
    while (end < result.length && result[end]._isMissing) end++
    const before = start - 1, after = end
    if (before >= 0 && after < result.length && result[before].rating != null && result[after].rating != null) {
      const a = result[before].rating, b = result[after].rating
      const len = after - before
      result[before].ratingGap = a
      result[after].ratingGap = b
      for (let j = start; j < end; j++) {
        const t = (j - before) / len
        result[j].ratingGap = +(a + t * (b - a)).toFixed(2)
      }
    }
    i = end
  }
  return { data: result, hasGaps }
}

/* ─────────── Sentiment-Distribution-Bar ─────────── */
/* Statt einer SVG-Gauge: cleane horizontale Verteilungs-Bar mit Markierung. */
function SentimentBar({ sentiment, rating }) {
  const meta = sentimentMeta(sentiment)
  // Position der Markierung (0 = ganz links / negativ, 100 = ganz rechts / positiv)
  // Berechnet aus Rating (1-5) → 0-100%
  const pct = Number.isFinite(Number(rating))
    ? Math.max(0, Math.min(100, ((Number(rating) - 1) / 4) * 100))
    : ((meta.value + 1) / 2) * 100

  // Sentiment-Verteilung als Stacked Segments
  const negPct = pct < 35 ? 70 : pct < 60 ? 30 : 15
  const posPct = pct >= 65 ? 70 : pct >= 40 ? 30 : 15
  const neuPct = 100 - negPct - posPct

  return (
    <div className="w-full">
      {/* Stacked Sentiment-Bar (Verteilung) */}
      <div className="relative">
        <div className="flex h-3 rounded-full overflow-hidden border border-slate-200 bg-white">
          <div className="bg-rose-500"     style={{ width: `${negPct}%` }} title={`Negativ: ${negPct}%`} />
          <div className="bg-slate-400"    style={{ width: `${neuPct}%` }} title={`Neutral: ${neuPct}%`} />
          <div className="bg-emerald-500"  style={{ width: `${posPct}%` }} title={`Positiv: ${posPct}%`} />
        </div>

        {/* Indicator-Pfeil über der Bar */}
        <div
          className="absolute -top-1.5 transition-all duration-300 ease-out"
          style={{ left: `calc(${pct}% - 6px)` }}
        >
          <div
            className="w-3 h-3 rotate-45 border-2 border-white shadow-sm"
            style={{ background: meta.color }}
          />
        </div>
      </div>

      {/* Skala-Beschriftung */}
      <div className="flex justify-between mt-2 text-[10px] font-mono uppercase tracking-wider">
        <span className="text-rose-700">Negativ</span>
        <span className="text-slate-500">Neutral</span>
        <span className="text-emerald-700">Positiv</span>
      </div>

      {/* Verteilungswerte als kleine Pills */}
      <div className="flex justify-center gap-2 mt-3">
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
          {negPct}% negativ
        </span>
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          {neuPct}% neutral
        </span>
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          {posPct}% positiv
        </span>
      </div>
    </div>
  )
}

/* ─────────── Collapsible — gestaffelte Animation ─────────── */
/* Öffnen: erst Höhe expandiert (320ms), DANN faded Content ein (200ms, delay 200ms) */
/* Schließen: erst Content fadet aus (200ms), DANN Höhe kollabiert (320ms, delay 180ms) */
function Collapsible({ open, children }) {
  return (
    <div className={["collapse-row", open ? "is-open" : ""].join(" ")}>
      <div className="collapse-inner">
        <div
          style={{
            opacity: open ? 1 : 0,
            transform: open ? "translateY(0)" : "translateY(-6px)",
            transition: open
              ? "opacity 220ms ease-out 200ms, transform 220ms ease-out 200ms"
              : "opacity 180ms ease-in, transform 180ms ease-in",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

/* ─────────── Section ─────────── */
function Section({ icon, title, eyebrow, action, children }) {
  return (
    <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
      <header className="px-4 py-3 border-b border-slate-200 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {icon && (
            <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[14px] [&_svg]:h-[14px]">
              {icon}
            </span>
          )}
          <div className="min-w-0">
            {eyebrow && (
              <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{eyebrow}</p>
            )}
            <h3 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900">{title}</h3>
          </div>
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </header>
      <div className="p-4">{children}</div>
    </section>
  )
}

/* ─────────── Custom Tooltip — slate-900 dark style ─────────── */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const point = payload[0]?.payload
  if (point?._isMissing) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[140px]">
        <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{label}</p>
        <p className="text-amber-400 inline-flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          Interpolierter Wert
        </p>
        {point.ratingGap != null && (
          <p className="flex items-center justify-between gap-3 mt-1">
            <span className="text-slate-400">Wert</span>
            <span className="font-semibold tnum text-amber-300">{fmt(point.ratingGap, 2)}</span>
          </p>
        )}
      </div>
    )
  }
  const ratingEntry = payload.find((p) => p.dataKey === "rating" && p.value != null)
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[140px]">
      <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{label}</p>
      {ratingEntry && (
        <p className="flex items-center justify-between gap-3">
          <span className="text-slate-400">Rating</span>
          <span className="font-semibold tnum text-white">{fmt(ratingEntry.value, 2)} / 5</span>
        </p>
      )}
    </div>
  )
}

/* ============================================================================
   TopicDetailModal
   ============================================================================ */
const VISIBILITY_DEFAULT = {
  stats:        true,
  timelineChart: true,
  sentimentChart: true,
  statements:   true,
  exampleReview: true,
}

export default function TopicDetailModal({ open, onOpenChange, topic, onBackToTable, sourceFilter, onSourceFilterChange }) {
  const [currentExampleIndex, setCurrentExampleIndex] = React.useState(3)
  const [timeFilter, setTimeFilter] = React.useState("all")
  const [reviewDetailModalOpen, setReviewDetailModalOpen] = React.useState(false)
  const [selectedReviewDetail, setSelectedReviewDetail] = React.useState(null)
  const [selectedReviewIndex, setSelectedReviewIndex] = React.useState(0)
  const [visibility, setVisibility] = React.useState(VISIBILITY_DEFAULT)
  const [viewPanelOpen, setViewPanelOpen] = React.useState(false)

  const toggleVisibility = (key) => setVisibility((v) => ({ ...v, [key]: !v[key] }))

  React.useEffect(() => { setCurrentExampleIndex(3) }, [topic])

  if (!topic) return null

  const meta = sentimentMeta(topic.sentiment)
  const tone = ratingTone(topic.avgRating)
  const isLimited = topic.statistical_meta?.risk_level === "limited"

  /* ── Timeline filtering ── */
  const filteredTimelineData = React.useMemo(() => {
    if (!topic.timelineData?.length) return []
    if (timeFilter === "all") return topic.timelineData
    const map = { "1y": 12, "6m": 6, "3m": 3, "1m": 1 }
    const monthsToShow = map[timeFilter] ?? 12
    const cutoff = new Date()
    cutoff.setMonth(cutoff.getMonth() - monthsToShow)
    return topic.timelineData.filter((it) => {
      if (!it.year || !it.monthNum) return false
      return new Date(it.year, it.monthNum - 1, 1) >= cutoff
    })
  }, [topic.timelineData, timeFilter])

  const { data: processedTimelineData, hasGaps: timelineHasGaps } = processTimelineDataWithGaps(filteredTimelineData)

  /* ── Reviews / Examples ── */
  // Sort example reviews (index 3+) by comment richness so the most complete ones appear first
  const sortedReviewDetails = React.useMemo(() => {
    const details = topic.reviewDetails || []
    if (details.length <= 3) return details
    const richness = (d) => {
      const fr = d?.fullReview || {}
      const fields = [
        fr.gut_am_arbeitgeber, fr.schlecht_am_arbeitgeber,
        fr.verbesserungsvorschlaege, fr.stellenbeschreibung, fr.jobbeschreibung,
      ]
      const filled = fields.filter((f) => f && f.trim().length > 20).length
      const totalLen = fields.reduce((s, f) => s + (f?.length || 0), 0)
      const bothBonus = (fr.gut_am_arbeitgeber?.trim().length > 20 && fr.schlecht_am_arbeitgeber?.trim().length > 20) ? 15 : 0
      return filled * 10 + bothBonus + Math.min(totalLen / 100, 20)
    }
    const top3 = details.slice(0, 3)
    const rest = details.slice(3).slice().sort((a, b) => richness(b) - richness(a))
    return [...top3, ...rest]
  }, [topic.reviewDetails])

  const totalExamples = topic.typicalStatements?.length || 0
  const reviewStartIndex = 3
  const reviewEndIndex   = Math.min(12, totalExamples - 1)
  const remainingExamples = Math.max(0, reviewEndIndex - reviewStartIndex + 1)
  const hasMultipleExamples = totalExamples > reviewStartIndex + 1

  const goToPrev = () => setCurrentExampleIndex((p) => p > reviewStartIndex ? p - 1 : reviewEndIndex)
  const goToNext = () => setCurrentExampleIndex((p) => p < reviewEndIndex   ? p + 1 : reviewStartIndex)

  const handleStatementClick = (index) => {
    const detail = sortedReviewDetails?.[index]
    if (detail?.fullReview) {
      setSelectedReviewDetail(detail)
      setSelectedReviewIndex(index)
      setReviewDetailModalOpen(true)
    }
  }

  const handleExampleClick = () => handleStatementClick(currentExampleIndex)

  const sentimentPercentage = Math.round(((Number(topic.avgRating) - 1) / 4) * 100)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="overflow-hidden flex flex-col p-0 gap-0"
        style={{ width: "88vw", maxWidth: "88vw", height: "88vh", maxHeight: "88vh" }}
      >
        {/* Tonaler Akzentbalken oben */}
        <span aria-hidden="true" className={`block h-[3px] w-full ${meta.accent}`} />

        {/* ── Header ── */}
        <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start justify-between gap-3 flex-shrink-0">
          <div className="flex items-start gap-3 min-w-0 flex-1">
            {onBackToTable && (
              <button
                onClick={onBackToTable}
                title="Zurück zur Tabelle"
                className="h-8 w-8 rounded-md grid place-items-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 flex-none mt-0.5"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
            )}
            <span className={`w-9 h-9 rounded-md grid place-items-center flex-none mt-0.5 ${meta.bg} ${meta.text} [&_svg]:w-[18px] [&_svg]:h-[18px]`}>
              <Tag />
            </span>
            <div className="min-w-0 flex-1">
              <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                TOPIC-DETAIL · ANALYSE
              </p>
              <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900 inline-flex items-center gap-2 flex-wrap">
                {topic.topic}
                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border ${meta.bg} ${meta.text} ${meta.border}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
                  {meta.label}
                </span>
                {isLimited && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold tracking-wider bg-rose-600 text-white">
                    <AlertTriangle className="h-3 w-3" />
                    BEGRENZT
                  </span>
                )}
              </DialogTitle>
              <p className="m-0 mt-1 text-[11px] text-slate-500">
                {topic.frequency} Erwähnungen · Ø {fmt(topic.avgRating, 2)} / 5
                {topic.statistical_meta?.review_count != null && ` · n=${topic.statistical_meta.review_count}`}
              </p>
            </div>
          </div>

          {/* Visibility-Panel Toggle (Ansicht anpassen) */}
          <button
            onClick={() => setViewPanelOpen((v) => !v)}
            title="Ansicht anpassen"
            className={[
              "h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium border flex-shrink-0",
              "transition-colors duration-200",
              "[&_svg]:flex-none [&_svg]:w-3.5 [&_svg]:h-3.5",
              "[&_svg]:transition-transform [&_svg]:duration-300",
              viewPanelOpen
                ? "bg-slate-900 text-white border-slate-900 [&_svg]:rotate-180"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50",
            ].join(" ")}
          >
            <Settings2 />
            Ansicht
          </button>
        </div>

        {/* Visibility-Panel — animiert via Collapsible */}
        <div className="flex-shrink-0">
          <Collapsible open={viewPanelOpen}>
            <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
              <p className="m-0 mb-2 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">
                Sichtbare Bereiche
              </p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { key: "stats",          label: "Kennzahlen" },
                  { key: "timelineChart",  label: "Zeitverlauf" },
                  { key: "sentimentChart", label: "Sentiment" },
                  { key: "statements",     label: "Aussagen" },
                  { key: "exampleReview",  label: "Beispiel-Review" },
                ].map((opt) => {
                  const active = visibility[opt.key]
                  return (
                    <button
                      key={opt.key}
                      onClick={() => toggleVisibility(opt.key)}
                      className={[
                        "h-7 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium border",
                        "transition-[background-color,color,border-color,box-shadow] duration-300 ease-out",
                        "[&_svg]:flex-none [&_svg]:w-3 [&_svg]:h-3 [&_svg]:transition-all [&_svg]:duration-300",
                        active
                          ? "bg-slate-900 text-white border-slate-900 shadow-sm [&_svg]:scale-110"
                          : "bg-white text-slate-500 border-slate-300 hover:text-slate-900 hover:bg-slate-100 [&_svg]:scale-100",
                      ].join(" ")}
                    >
                      {active ? <Eye /> : <EyeOff />}
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>
          </Collapsible>
        </div>

        {/* ── Body (scrollable) ── */}
        <div className="flex-1 overflow-y-auto bg-slate-50">
          <div className="flex flex-col p-5">

            {/* Stats — 3 tonal cards */}
            <Collapsible open={visibility.stats}>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-white border border-slate-200 rounded-md px-4 py-3.5 text-center">
                <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Erwähnungen</p>
                <p className="text-[26px] font-semibold tnum text-slate-900 leading-tight">
                  {Number(topic.frequency).toLocaleString("de-DE")}
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">Reviews mit diesem Topic</p>
              </div>
              <div className={`bg-white border rounded-md px-4 py-3.5 text-center ${tone.border}`}>
                <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Ø Rating</p>
                <p className={`text-[26px] font-semibold tnum leading-tight ${tone.text}`}>
                  {fmt(topic.avgRating, 2)}
                </p>
                <div className="mt-1.5 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <div className={`h-full ${tone.bar}`} style={{ width: `${(Number(topic.avgRating) / 5) * 100}%` }} />
                </div>
              </div>
              <div className={`bg-white border rounded-md px-4 py-3.5 text-center ${meta.border}`}>
                <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Sentiment</p>
                <p className={`text-[20px] font-semibold leading-tight ${meta.text}`}>{meta.label}</p>
                <p className="text-[11px] text-slate-500 mt-1 tnum">{sentimentPercentage}% Stimmung</p>
              </div>
            </div>
            </Collapsible>

            {/* Charts row: Timeline + Sentiment Gauge */}
            <Collapsible open={visibility.timelineChart || visibility.sentimentChart}>
            <div className={`grid grid-cols-1 gap-4 mb-4 transition-all duration-300 ${
              visibility.timelineChart && visibility.sentimentChart
                ? "lg:grid-cols-3"
                : "lg:grid-cols-1"
            }`}>
              {visibility.timelineChart && (
              <div className={visibility.sentimentChart ? "lg:col-span-2" : ""}>
                <Section
                  icon={<StarIcon />}
                  eyebrow="ZEITREIHE"
                  title="Bewertung über Zeit"
                  action={
                    <DropdownPicker
                      label="Zeit"
                      value={
                        timeFilter === "all" ? "Gesamt"
                          : timeFilter === "1y" ? "1 Jahr"
                          : timeFilter === "6m" ? "6 Monate"
                          : timeFilter === "3m" ? "3 Monate"
                          : "1 Monat"
                      }
                      compact={false}
                      options={[
                        { value: "all", label: "Gesamt" },
                        { value: "1y",  label: "1 Jahr" },
                        { value: "6m",  label: "6 Monate" },
                        { value: "3m",  label: "3 Monate" },
                        { value: "1m",  label: "1 Monat" },
                      ]}
                      onChange={setTimeFilter}
                    />
                  }
                >
                  <div className="h-[280px] w-full">
                    {processedTimelineData.length === 0 ? (
                      <div className="h-full flex items-center justify-center">
                        <p className="text-[13px] text-slate-500">Keine Daten für diesen Zeitraum</p>
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={processedTimelineData} margin={{ top: 8, right: 16, left: 0, bottom: 5 }}>
                          <defs>
                            <linearGradient id="topicRatingGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%"   stopColor={tone.hex} stopOpacity={0.20} />
                              <stop offset="100%" stopColor={tone.hex} stopOpacity={0.0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="2 4" stroke="#f1f5f9" vertical={false} />
                          <XAxis
                            dataKey="month"
                            tick={{ fontSize: 10, fill: "#94a3b8" }}
                            tickLine={false}
                            axisLine={{ stroke: "#e2e8f0" }}
                            interval="preserveStartEnd"
                            tickMargin={8}
                          />
                          <YAxis
                            domain={[0, 5]}
                            tick={{ fontSize: 10, fill: "#94a3b8" }}
                            tickLine={false}
                            axisLine={false}
                            width={32}
                            ticks={[0, 1, 2, 3, 4, 5]}
                            tickFormatter={(v) => v.toFixed(1)}
                          />
                          <Tooltip
                            content={<ChartTooltip />}
                            cursor={{ stroke: "#cbd5e1", strokeWidth: 1, strokeDasharray: "3 3" }}
                          />
                          <Area
                            type="monotone"
                            dataKey="rating"
                            stroke={tone.hex}
                            strokeWidth={2}
                            fill="url(#topicRatingGradient)"
                            dot={false}
                            activeDot={{ r: 4, fill: tone.hex, stroke: "#fff", strokeWidth: 2 }}
                            connectNulls={false}
                          />
                          {timelineHasGaps && (
                            <Line
                              type="monotone"
                              dataKey="ratingGap"
                              stroke="#94a3b8"
                              strokeWidth={2}
                              strokeDasharray="6 4"
                              strokeOpacity={0.85}
                              dot={false}
                              activeDot={false}
                              connectNulls={false}
                              isAnimationActive={false}
                            />
                          )}
                        </ComposedChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                  {timelineHasGaps && (
                    <p className="mt-2 text-[11px] text-slate-500 text-center italic flex items-center justify-center gap-1.5">
                      <span className="inline-block w-5 h-0 border-t border-dashed border-slate-400" />
                      Gestrichelte Linie = interpolierte Werte
                    </p>
                  )}
                </Section>
              </div>
              )}
              {visibility.sentimentChart && (
              <Section icon={<BarChart3 />} eyebrow="STIMMUNG" title="Sentiment-Verteilung">
                {/* Großer Sentiment-Wert oben */}
                <div className="text-center mb-4">
                  <p className={`text-[36px] font-semibold tnum tracking-tight leading-none ${meta.text}`}>
                    {sentimentPercentage}%
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Gesamtstimmung · <span className={`font-semibold ${meta.text}`}>{meta.label}</span>
                  </p>
                </div>

                {/* Horizontal Sentiment-Bar */}
                <SentimentBar sentiment={topic.sentiment} rating={topic.avgRating} />
              </Section>
              )}
            </div>
            </Collapsible>

            {/* Typische Aussagen */}
            <Collapsible open={visibility.statements && topic.typicalStatements?.length > 0}>
            <div className="mb-4">
              <Section icon={<Quote />} eyebrow="ZITATE" title="Typische Aussagen">
                <ul className="space-y-2">
                  {topic.typicalStatements.slice(0, 3).map((statement, index) => (
                    <li
                      key={index}
                      onClick={() => handleStatementClick(index)}
                      title="Klicken für vollständige Review"
                      className="group relative flex items-start gap-3 p-3 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-md cursor-pointer transition-colors"
                    >
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center font-mono text-[11px] font-bold text-slate-600">
                        {index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] text-slate-700 leading-relaxed italic">
                          „{statement}"
                        </p>
                        <p className="text-[11px] text-blue-600 mt-1.5 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                          → Vollständige Review öffnen
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </Section>
            </div>
            </Collapsible>

            {/* Beispiel-Review mit Navigation */}
            <Collapsible open={visibility.exampleReview && !!(topic.typicalStatements?.[currentExampleIndex] || topic.example)}>
            <div className="mb-4">
              <Section
                icon={<MessageSquare />}
                eyebrow="EINZEL-REVIEW"
                title="Beispiel-Review"
                action={hasMultipleExamples && (
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] tnum text-slate-500">
                      {currentExampleIndex - reviewStartIndex + 1} / {remainingExamples}
                    </span>
                    <div className="inline-flex">
                      <button
                        onClick={goToPrev}
                        className="h-7 w-7 inline-flex items-center justify-center rounded-l-md border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      >
                        <ChevronLeft className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={goToNext}
                        className="h-7 w-7 inline-flex items-center justify-center rounded-r-md border border-l-0 border-slate-300 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      >
                        <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              >
                {(() => {
                  const hasFullReview = !!sortedReviewDetails?.[currentExampleIndex]?.fullReview
                  return (
                    <div
                      onClick={hasFullReview ? handleExampleClick : undefined}
                      className={[
                        "p-4 bg-slate-50 border border-slate-200 rounded-md transition-colors group",
                        hasFullReview ? "cursor-pointer hover:bg-blue-50 hover:border-blue-300" : "cursor-default",
                      ].join(" ")}
                    >
                      <p className="text-[13px] text-slate-700 italic leading-relaxed">
                        „{topic.typicalStatements?.[currentExampleIndex] || topic.example}"
                      </p>
                      {hasFullReview && (
                        <p className="text-[11px] text-blue-600 mt-2 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                          → Vollständige Review öffnen
                        </p>
                      )}
                    </div>
                  )
                })()}
              </Section>
            </div>
            </Collapsible>
          </div>
        </div>

        {/* Review Detail Modal */}
        <ReviewDetailModal
          open={reviewDetailModalOpen}
          onOpenChange={setReviewDetailModalOpen}
          reviewDetail={selectedReviewDetail}
          allReviewDetails={sortedReviewDetails}
          currentIndex={selectedReviewIndex}
          onNavigate={(idx) => {
            if (sortedReviewDetails?.[idx]) {
              setSelectedReviewDetail(sortedReviewDetails[idx])
              setSelectedReviewIndex(idx)
            }
          }}
        />
      </DialogContent>
    </Dialog>
  )
}
