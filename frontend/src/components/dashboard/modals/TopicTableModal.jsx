import * as React from "react"
import { useState, useMemo } from "react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Search, AlertTriangle, ArrowUp, ArrowDown, ArrowUpDown, X } from "lucide-react"
import { SourceToggle } from "../ChartHeader"
import { Tag } from "../../../icons"

const SOURCE_OPTIONS = [
  { value: "all",        label: "Alle",        color: "#64748b" },
  { value: "employee",   label: "Mitarbeiter", color: "#3b82f6" },
  { value: "candidates", label: "Bewerber",    color: "#10b981" },
]

const SOURCE_LABEL = {
  all:        "Alle Quellen",
  employee:   "Mitarbeiter",
  candidates: "Bewerber",
}

/* ── Tonal helpers ── */
const ratingTone = (s) => {
  const n = Number(s)
  if (!Number.isFinite(n)) return { text: "text-slate-700", bar: "bg-slate-300" }
  if (n >= 3.5) return { text: "text-emerald-700", bar: "bg-emerald-500" }
  if (n >= 2.5) return { text: "text-amber-700",   bar: "bg-amber-500" }
  return            { text: "text-rose-700",    bar: "bg-rose-500" }
}

const sentimentBadge = (sentiment) => {
  const s = String(sentiment || "").toLowerCase()
  // Border + leichte Sättigung damit Badges auch auf eingefärbten Zeilen kontrastieren
  if (s.includes("pos")) return { cls: "bg-emerald-50 text-emerald-700 border border-emerald-300", dot: "bg-emerald-500" }
  if (s.includes("neg")) return { cls: "bg-rose-50 text-rose-700 border border-rose-300",          dot: "bg-rose-500" }
  if (s.includes("neu")) return { cls: "bg-slate-50 text-slate-600 border border-slate-300",       dot: "bg-slate-400" }
  return { cls: "bg-slate-50 text-slate-600 border border-slate-300", dot: "bg-slate-400" }
}

const riskBadge = (statistical_meta) => {
  if (!statistical_meta) return null
  const { risk_level } = statistical_meta
  switch (risk_level) {
    case "limited":     return { cls: "bg-rose-50 text-rose-600 border-rose-200",              text: "Begrenzt" }
    case "constrained": return { cls: "bg-amber-50 text-amber-700 border-amber-200",          text: "Eingeschränkt" }
    case "acceptable":  return { cls: "bg-blue-50 text-blue-700 border-blue-200",             text: "Akzeptabel" }
    case "solid":       return { cls: "bg-emerald-50 text-emerald-700 border-emerald-200",    text: "Solide" }
    default:            return null
  }
}

const fmt = (n, d = 1) => Number.isFinite(Number(n)) ? Number(n).toFixed(d).replace(".", ",") : "—"

export default function TopicTableModal({
  open, onOpenChange, topics, onTopicSelect, sourceFilter, onSourceFilterChange,
}) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortKey, setSortKey] = useState("frequency") // topic | frequency | rating
  const [sortDir, setSortDir] = useState("desc")
  const [sentimentFilter, setSentimentFilter] = useState("all") // all | positive | negative | neutral
  const [bannerDismissed, setBannerDismissed] = useState(false)

  const sourceValue = sourceFilter || "all"

  // Sentiment-Counts (für Filter-Badges)
  const sentimentCounts = useMemo(() => {
    const c = { all: topics.length, positive: 0, negative: 0, neutral: 0 }
    for (const t of topics) {
      const s = String(t.sentiment || "").toLowerCase()
      if (s.includes("pos")) c.positive += 1
      else if (s.includes("neg")) c.negative += 1
      else if (s.includes("neu")) c.neutral += 1
    }
    return c
  }, [topics])

  // Filter + Sort
  const filteredTopics = useMemo(() => {
    const q = searchTerm.trim().toLowerCase()
    let list = topics

    // Sentiment-Filter
    if (sentimentFilter !== "all") {
      list = list.filter((t) => {
        const s = String(t.sentiment || "").toLowerCase()
        if (sentimentFilter === "positive") return s.includes("pos")
        if (sentimentFilter === "negative") return s.includes("neg")
        if (sentimentFilter === "neutral")  return s.includes("neu")
        return true
      })
    }

    if (q) {
      list = list.filter((t) =>
        t.topic.toLowerCase().includes(q) ||
        (t.example || "").toLowerCase().includes(q)
      )
    }
    const dir = sortDir === "desc" ? -1 : 1
    return [...list].sort((a, b) => {
      if (sortKey === "topic") return dir * a.topic.localeCompare(b.topic, "de", { sensitivity: "base" })
      if (sortKey === "rating") return dir * ((Number(a.avgRating) || 0) - (Number(b.avgRating) || 0))
      return dir * ((Number(a.frequency) || 0) - (Number(b.frequency) || 0))
    })
  }, [topics, searchTerm, sortKey, sortDir, sentimentFilter])

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    else { setSortKey(key); setSortDir(key === "topic" ? "asc" : "desc") }
  }

  // Stats
  const stats = useMemo(() => {
    if (!topics.length) return null
    const total = topics.length
    const avg = topics.reduce((s, t) => s + (Number(t.avgRating) || 0), 0) / total
    const mentions = topics.reduce((s, t) => s + (Number(t.frequency) || 0), 0)
    const limited = topics.filter((t) => t.statistical_meta?.risk_level === "limited").length
    return { total, avg, mentions, limited }
  }, [topics])

  const SortHeader = ({ label, sortable, keyName, align = "left" }) => {
    const isActive = sortKey === keyName
    return (
      <button
        type="button"
        onClick={sortable ? () => toggleSort(keyName) : undefined}
        className={[
          "inline-flex items-center gap-1 font-mono text-[10px] tracking-[0.06em] uppercase",
          align === "center" ? "justify-center" : align === "right" ? "justify-end" : "justify-start",
          sortable ? "cursor-pointer hover:text-slate-900" : "cursor-default",
          isActive ? "text-slate-900" : "text-slate-500",
        ].join(" ")}
      >
        {label}
        {sortable && (
          isActive
            ? (sortDir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)
            : <ArrowUpDown className="h-3 w-3 opacity-40" />
        )}
      </button>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="overflow-hidden flex flex-col p-0 gap-0"
        style={{ width: "92vw", maxWidth: "92vw", height: "88vh", maxHeight: "88vh" }}
      >
        {/* Tonaler Akzentbalken oben (slate für neutral) */}
        <span aria-hidden="true" className="block h-[3px] w-full bg-slate-700" />

        {/* Header — gleiche Struktur wie TopicRating-Modal */}
        <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start justify-between gap-3 flex-shrink-0">
          <div className="flex items-start gap-2.5">
            <span className="w-9 h-9 rounded-md grid place-items-center bg-slate-100 text-slate-600 flex-none">
              <Tag className="w-[18px] h-[18px]" />
            </span>
            <div>
              <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                TOPIC-ÜBERSICHT · DETAILANSICHT
              </p>
              <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900">
                Alle Topics
              </DialogTitle>
              <p className="m-0 mt-0.5 text-[11px] text-slate-500">
                {SOURCE_LABEL[sourceValue]}{stats ? ` · ${stats.total} Topics · ${Number(stats.mentions).toLocaleString("de-DE")} Erwähnungen` : ""}
              </p>
            </div>
          </div>
          <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 flex-shrink-0">
            <SourceToggle
              value={sourceValue}
              onChange={(v) => onSourceFilterChange(v === "all" ? null : v)}
              options={SOURCE_OPTIONS}
            />
          </div>
        </div>

        {/* Toolbar: Suche + Sentiment-Filter + Stats */}
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-50 flex flex-col gap-3 flex-shrink-0">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-[320px]">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Topic oder Beispiel suchen…"
                className="h-8 pl-8 text-[13px] bg-white"
              />
            </div>

            {/* Sentiment-Filter (Segmented Control mit farbigen Punkten + Counts) */}
            <div role="tablist" aria-label="Sentiment-Filter" className="inline-flex bg-white border border-slate-300 rounded-md p-0.5">
              {[
                { value: "all",      label: "Alle",     dot: null,             count: sentimentCounts.all },
                { value: "positive", label: "Positiv",  dot: "bg-emerald-500", count: sentimentCounts.positive },
                { value: "neutral",  label: "Neutral",  dot: "bg-slate-400",   count: sentimentCounts.neutral },
                { value: "negative", label: "Negativ",  dot: "bg-rose-500",    count: sentimentCounts.negative },
              ].map((opt) => {
                const active = sentimentFilter === opt.value
                return (
                  <button
                    key={opt.value}
                    role="tab"
                    aria-selected={active}
                    onClick={() => setSentimentFilter(opt.value)}
                    className={[
                      "h-7 px-2.5 inline-flex items-center gap-1.5 rounded-[5px] text-[12px] font-medium transition-colors",
                      active ? "bg-slate-900 text-white shadow-sm" : "text-slate-600 hover:text-slate-900",
                    ].join(" ")}
                  >
                    {opt.dot && (
                      <span className={`w-1.5 h-1.5 rounded-full flex-none ${opt.dot}`} aria-hidden="true" />
                    )}
                    <span>{opt.label}</span>
                    <span className={[
                      "tnum text-[11px] px-1 rounded",
                      active ? "bg-white/20 text-white" : "text-slate-500",
                    ].join(" ")}>
                      {opt.count}
                    </span>
                  </button>
                )
              })}
            </div>

            {stats && (
              <div className="flex items-center gap-4 text-[12px] text-slate-600 ml-auto">
                <span className="inline-flex items-center gap-1.5">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">Ø Rating</span>
                  <span className={`font-semibold tnum ${ratingTone(stats.avg).text}`}>
                    {fmt(stats.avg, 2)}
                  </span>
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">Treffer</span>
                  <span className="font-semibold tnum text-slate-900">{filteredTopics.length}</span>
                </span>
              </div>
            )}
          </div>

          {/* Warning Banner für begrenzte Datenbasis */}
          {stats?.limited > 0 && !bannerDismissed && (
            <div className="rounded-md bg-rose-50 border-2 border-rose-300 overflow-hidden">
              {/* Akzentbalken oben */}
              <div className="h-[3px] bg-rose-500" />
              <div className="px-3 py-2.5 flex items-start gap-2.5">
                <span className="w-7 h-7 rounded-md grid place-items-center bg-rose-100 text-rose-700 flex-none">
                  <AlertTriangle className="h-4 w-4" />
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-[12.5px] font-semibold text-rose-900 leading-tight">
                    Achtung: Begrenzte Datenbasis bei {stats.limited} Topic{stats.limited !== 1 ? "s" : ""}
                  </p>
                  <p className="text-[11px] text-rose-700 mt-0.5 leading-snug">
                    Diese Topics haben weniger als 30 Reviews. Statistische Aussagen sind eingeschränkt — Ergebnisse mit Vorsicht interpretieren.
                  </p>
                </div>
                <span className="inline-flex items-center px-2 py-1 rounded-full bg-rose-600 text-white text-[11px] font-bold tnum flex-none">
                  {stats.limited}
                </span>
                <button
                  onClick={() => setBannerDismissed(true)}
                  className="text-rose-400 hover:text-rose-600 flex-none transition-colors"
                  aria-label="Hinweis schließen"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Tabelle */}
        <div className="flex-1 overflow-auto min-h-0">
          {filteredTopics.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-[13px] text-slate-500">Keine Topics gefunden</p>
            </div>
          ) : (
            <table className="w-full text-[13px]">
              <thead className="sticky top-0 bg-slate-50/80 backdrop-blur-sm border-b border-slate-200 z-10">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium text-slate-500"><SortHeader label="Topic"      sortable keyName="topic" /></th>
                  <th className="text-center px-3 py-2.5 font-medium text-slate-500 w-[100px]"><SortHeader label="Erwähnungen" sortable keyName="frequency" align="center" /></th>
                  <th className="text-center px-3 py-2.5 font-medium text-slate-500 w-[110px]"><SortHeader label="Ø Rating"   sortable keyName="rating"    align="center" /></th>
                  <th className="text-center px-3 py-2.5 font-medium text-slate-500 w-[110px]"><SortHeader label="Sentiment"  align="center" /></th>
                  <th className="text-center px-3 py-2.5 font-medium text-slate-500 w-[120px]"><SortHeader label="Datenqualität" align="center" /></th>
                  <th className="text-left px-4 py-2.5 font-medium text-slate-500"><SortHeader label="Beispiel" /></th>
                </tr>
              </thead>
              <tbody>
                {filteredTopics.map((topic) => {
                  const isRisky = topic.statistical_meta?.risk_level === "limited"
                  const tone = ratingTone(topic.avgRating)
                  const sBadge = sentimentBadge(topic.sentiment)
                  const rBadge = riskBadge(topic.statistical_meta)
                  return (
                    <tr
                      key={topic.id}
                      className={[
                        "border-b border-slate-100 cursor-pointer transition-colors relative",
                        "hover:bg-slate-50",
                      ].join(" ")}
                      onClick={() => onTopicSelect(topic)}
                    >
                      <td className={`px-4 py-3 relative ${isRisky ? "pl-3" : ""}`}>
                        {/* Linker Status-Balken bei begrenzter Datenbasis (full row height) */}
                        {isRisky && (
                          <span
                            aria-hidden="true"
                            className="absolute left-0 top-0 bottom-0 w-[4px] bg-rose-300"
                          />
                        )}
                        <div className="flex items-center gap-2">
                          {isRisky && (
                            <span
                              title="Begrenzte Datenbasis (< 30 Reviews) — Ergebnisse mit Vorsicht interpretieren"
                              className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-rose-50 text-rose-400 flex-none ring-1 ring-rose-200"
                            >
                              <AlertTriangle className="h-3 w-3" />
                            </span>
                          )}
                          <span className="font-medium text-slate-900">
                            {topic.topic}
                          </span>
                          {isRisky && topic.statistical_meta?.review_count != null && (
                            <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded">
                              n={topic.statistical_meta.review_count}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-center font-medium tnum text-slate-700">
                        {Number(topic.frequency).toLocaleString("de-DE")}
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2 justify-center">
                          <div className="h-1.5 w-12 rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className={`h-full ${tone.bar}`}
                              style={{ width: `${Math.min(100, (Number(topic.avgRating) / 5) * 100)}%` }}
                            />
                          </div>
                          <span className={`font-semibold tnum text-[13px] ${tone.text} w-[32px] text-right`}>
                            {fmt(topic.avgRating, 1)}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium ${sBadge.cls}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${sBadge.dot}`} />
                          {topic.sentiment}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-center">
                        {rBadge ? (
                          <span className={[
                            "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] border",
                            rBadge.bold ? "font-bold tracking-wider" : "font-medium",
                            rBadge.cls,
                          ].join(" ")}>
                            {rBadge.bold && <AlertTriangle className="h-3 w-3" />}
                            {rBadge.text}
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        <p className="line-clamp-2 italic text-[12.5px] leading-snug">
                          {topic.example || "—"}
                        </p>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-2.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between flex-shrink-0 gap-3 flex-wrap">
          <div className="flex items-center gap-3 text-[11px] text-slate-500">
            <span>
              <span className="font-medium tnum text-slate-700">{filteredTopics.length}</span>
              {" / "}
              <span className="tnum">{topics.length}</span>
              {" Topics"}
            </span>
            {sentimentFilter !== "all" && (
              <span className="inline-flex items-center gap-1">
                <span>·</span>
                <span>Filter:</span>
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700 font-medium">
                  {sentimentFilter === "positive" && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
                  {sentimentFilter === "negative" && <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />}
                  {sentimentFilter === "neutral"  && <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />}
                  {sentimentFilter === "positive" ? "Positiv" : sentimentFilter === "negative" ? "Negativ" : "Neutral"}
                </span>
                <button
                  onClick={() => setSentimentFilter("all")}
                  className="text-blue-600 hover:text-blue-800 underline-offset-2 hover:underline"
                >
                  zurücksetzen
                </button>
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-500">
            Zeile anklicken öffnet Details
          </span>
        </div>
      </DialogContent>
    </Dialog>
  )
}
