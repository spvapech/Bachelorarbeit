import * as React from "react"
import { useState, useEffect, useMemo, useCallback, memo } from "react"
import {
    AlertTriangle, ExternalLink, RefreshCw, Sparkles, Filter,
    TrendingDown, TrendingUp, Newspaper, Megaphone, CandlestickChart, FileText,
} from "lucide-react"
import { API_URL } from "@/config"
import { ChartCardHeader, DropdownPicker } from "./ChartHeader"

const MONTH_NAMES_LONG = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

function periodLabel(period) {
    const [y, m] = String(period).split("-").map(Number)
    if (!Number.isFinite(y) || !Number.isFinite(m)) return period
    return `${MONTH_NAMES_LONG[m - 1]} ${y}`
}

const fmtDelta = (direction, magnitude) => {
    const v = Math.abs(Number(magnitude) || 0).toFixed(2).replace(".", ",")
    return direction === "fall" ? `−${v}` : `+${v}`
}

/* Quelltyp → Badge-Stil + Label */
const SOURCE_BADGES = {
    news: { label: "News", cls: "bg-blue-50 text-blue-700 border-blue-200", icon: Newspaper },
    adhoc: { label: "Ad-hoc", cls: "bg-amber-50 text-amber-700 border-amber-200", icon: Megaphone },
    stock_move: { label: "Kursbewegung", cls: "bg-violet-50 text-violet-700 border-violet-200", icon: CandlestickChart },
    manual: { label: "Manuell", cls: "bg-slate-100 text-slate-600 border-slate-200", icon: FileText },
}

function SourceBadge({ quelle }) {
    const key = quelle?.source_type in SOURCE_BADGES ? quelle.source_type : "manual"
    const badge = SOURCE_BADGES[key]
    const Icon = badge.icon
    return (
        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-medium ${badge.cls}`}>
            <Icon className="w-3 h-3" />
            {badge.label}
        </span>
    )
}

/* ============================================================================
   AnomalyExplanationsCard — Anomalieliste mit Erklärungsansätzen und
   Quellenbelegen (2. Design-Zyklus). Volle Breite: links Anomalien,
   rechts Erklärungen der ausgewählten Anomalie.
   ============================================================================ */
export const AnomalyExplanationsCard = memo(function AnomalyExplanationsCard({ companyId }) {
    const [items, setItems] = useState([])            // [{anomaly, explanations}]
    const [coverage, setCoverage] = useState(null)
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)
    const [error, setError] = useState(null)
    const [selectedId, setSelectedId] = useState(null)
    const [dimensionFilter, setDimensionFilter] = useState("Nur Gesamtbewertung")

    const fetchData = useCallback(async () => {
        if (!companyId) return
        try {
            setError(null)
            const res = await fetch(`${API_URL}/explanations/company/${companyId}`)
            if (!res.ok) throw new Error(`API Error (explanations): ${res.status}`)
            const json = await res.json()
            setItems(json.items || [])
            setCoverage(json.coverage || null)
        } catch (e) {
            console.error("Error fetching explanations:", e)
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }, [companyId])

    useEffect(() => {
        if (!companyId) { setLoading(false); setItems([]); setCoverage(null); return }
        setLoading(true)
        setSelectedId(null)
        fetchData()
    }, [companyId, fetchData])

    const generate = async () => {
        if (!companyId) return
        setGenerating(true)
        try {
            // Sicherstellen, dass Anomalien erkannt sind (Autodetect), dann generieren
            await fetch(`${API_URL}/anomalies/company/${companyId}?source=employee`)
            const res = await fetch(`${API_URL}/explanations/company/${companyId}/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({}),
            })
            if (!res.ok) throw new Error(`Generierung fehlgeschlagen (${res.status})`)
            await fetchData()
        } catch (e) {
            console.error("Error generating explanations:", e)
            setError(e.message)
        } finally {
            setGenerating(false)
        }
    }

    const filteredItems = useMemo(() => {
        const filtered = dimensionFilter === "Nur Gesamtbewertung"
            ? items.filter((it) => it.anomaly.dimension === "durchschnittsbewertung")
            : items
        return [...filtered].sort((a, b) => String(a.anomaly.period).localeCompare(String(b.anomaly.period)))
    }, [items, dimensionFilter])

    const selected = useMemo(() => {
        if (filteredItems.length === 0) return null
        return filteredItems.find((it) => it.anomaly.id === selectedId) || filteredItems[0]
    }, [filteredItems, selectedId])

    const coverageLabel = coverage?.total_anomalies
        ? `${Math.round((coverage.coverage || 0) * 100)} % · ${coverage.anomalies_with_explanation}/${coverage.total_anomalies}`
        : null

    const hasAnyExplanations = items.some((it) => it.explanations.length > 0)

    const evidence = selected?.explanations[0]?.review_evidence

    return (
        <div className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow flex flex-col">
            <ChartCardHeader
                icon={<AlertTriangle />}
                eyebrow="ANOMALIEN · ERKLÄRUNGEN & QUELLEN"
                title="Anomalien & Erklärungsansätze"
                subtitle="Extreme Bewertungsveränderungen, verknüpft mit externen Ereignissen"
                actions={
                    <>
                        <DropdownPicker
                            label="Dimension"
                            value={dimensionFilter}
                            icon={<Filter />}
                            compact
                            options={[
                                { value: "Nur Gesamtbewertung", label: "Nur Gesamtbewertung" },
                                { value: "Alle Dimensionen", label: "Alle Dimensionen" },
                            ]}
                            onChange={setDimensionFilter}
                        />
                        {coverageLabel && (
                            <span
                                title="Erklärungsabdeckung: Anteil der Anomalien mit mindestens einem Erklärungsansatz (DZ2)"
                                className="h-7 inline-flex items-center gap-1.5 px-2.5 rounded-md border border-emerald-200 bg-emerald-50 text-emerald-700 text-[12px] font-medium"
                            >
                                Abdeckung {coverageLabel}
                            </span>
                        )}
                        <button
                            onClick={generate}
                            disabled={generating || !companyId}
                            className="h-7 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50 transition-colors"
                        >
                            {generating
                                ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                : <Sparkles className="w-3.5 h-3.5" />}
                            {generating ? "Generiere…" : "Erklärungen generieren"}
                        </button>
                    </>
                }
            />

            <div className="relative min-h-[220px]">
                {loading ? (
                    <div className="absolute inset-0 bg-white/70 flex items-center justify-center pointer-events-none">
                        <div className="flex items-center gap-2">
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                            <p className="text-slate-600 text-[12px]">Lade Anomalien…</p>
                        </div>
                    </div>
                ) : !companyId ? (
                    <div className="h-[220px] flex items-center justify-center">
                        <p className="text-[13px] text-slate-500">Keine Firma ausgewählt</p>
                    </div>
                ) : error ? (
                    <div className="h-[220px] flex items-center justify-center">
                        <p className="text-[13px] text-slate-500">Fehler: {error}</p>
                    </div>
                ) : filteredItems.length === 0 ? (
                    <div className="h-[220px] flex flex-col items-center justify-center gap-2 px-6 text-center">
                        <p className="text-[13px] text-slate-500 m-0">
                            Keine Anomalien erkannt. Die Erkennung läuft automatisch beim Laden der Timeline —
                            alternativ „Erklärungen generieren“ anklicken.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr]">
                        {/* Linke Spalte: Anomalieliste */}
                        <div className="border-b lg:border-b-0 lg:border-r border-slate-200 max-h-[420px] overflow-y-auto">
                            {filteredItems.map((it) => {
                                const a = it.anomaly
                                const isSelected = selected?.anomaly.id === a.id
                                const isFall = a.direction === "fall"
                                return (
                                    <button
                                        key={a.id}
                                        onClick={() => setSelectedId(a.id)}
                                        className={[
                                            "w-full text-left px-4 py-2.5 border-b border-slate-100 transition-colors",
                                            isSelected ? "bg-slate-50 border-l-2 border-l-slate-900" : "hover:bg-slate-50 border-l-2 border-l-transparent",
                                        ].join(" ")}
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-[13px] font-medium text-slate-900">{periodLabel(a.period)}</span>
                                            <span className={`inline-flex items-center gap-1 text-[12px] font-semibold tnum ${isFall ? "text-rose-600" : "text-emerald-600"}`}>
                                                {isFall ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                                                {fmtDelta(a.direction, a.magnitude)}
                                            </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-2 mt-1">
                                            <span className="text-[11px] text-slate-500 truncate">{a.dimension_label}</span>
                                            <span className="flex items-center gap-1.5 flex-none">
                                                <span className="font-mono text-[9px] tracking-wide uppercase px-1 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200">
                                                    {a.method}
                                                </span>
                                                {it.explanations.length > 0 && (
                                                    <span className="text-[10px] text-slate-400 tnum">{it.explanations.length} Erkl.</span>
                                                )}
                                            </span>
                                        </div>
                                    </button>
                                )
                            })}
                        </div>

                        {/* Rechte Spalte: Erklärungen der ausgewählten Anomalie */}
                        <div className="px-4 py-3 max-h-[420px] overflow-y-auto">
                            {selected && (
                                <>
                                    <div className="flex items-baseline justify-between gap-3 flex-wrap mb-2">
                                        <h4 className="m-0 text-[13px] font-semibold text-slate-900">
                                            {selected.anomaly.direction === "fall" ? "Einbruch" : "Anstieg"} · {selected.anomaly.dimension_label} · {periodLabel(selected.anomaly.period)}
                                        </h4>
                                        <span className="text-[11px] text-slate-500">
                                            Ereignisfenster {String(selected.anomaly.window_start).slice(0, 10)} – {String(selected.anomaly.window_end).slice(0, 10)}
                                        </span>
                                    </div>

                                    {evidence && (
                                        <p className="text-[11px] text-slate-500 m-0 mb-3">
                                            Reviews im Fenster: {evidence.review_count}
                                            {evidence.sentiment && (
                                                <>
                                                    {" · Sentiment: "}
                                                    <span className="text-emerald-600">{evidence.sentiment.positive}+</span>{" / "}
                                                    <span className="text-slate-500">{evidence.sentiment.neutral}○</span>{" / "}
                                                    <span className="text-rose-600">{evidence.sentiment.negative}−</span>
                                                </>
                                            )}
                                        </p>
                                    )}

                                    {selected.explanations.length === 0 ? (
                                        <div className="border border-dashed border-slate-300 rounded-md px-4 py-6 text-center">
                                            <p className="text-[13px] text-slate-500 m-0">
                                                {hasAnyExplanations
                                                    ? "Kein Erklärungsansatz für diese Anomalie gefunden — Kontextdaten aktualisieren oder manuell importieren."
                                                    : "Noch keine Erklärungen generiert — oben „Erklärungen generieren“ anklicken."}
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col gap-2.5">
                                            {selected.explanations.map((exp) => (
                                                <div key={exp.id} className="border border-slate-200 rounded-md p-3 bg-white hover:border-slate-300 transition-colors">
                                                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1.5">
                                                        <div className="flex items-center gap-1.5">
                                                            <SourceBadge quelle={exp.quelle} />
                                                            {exp.quelle?.provider && exp.quelle.provider !== "manual" && (
                                                                <span className="text-[10px] text-slate-400">{exp.quelle.provider}</span>
                                                            )}
                                                            {exp.direction_consistent === true && (
                                                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-200">
                                                                    Richtung konsistent
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-1.5" title="Korrespondenz-Score (zeitlich + thematisch + Richtung)">
                                                            <div className="w-16 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                                                                <div
                                                                    className="h-full rounded-full bg-slate-700"
                                                                    style={{ width: `${Math.round((Number(exp.correspondence_score) || 0) * 100)}%` }}
                                                                />
                                                            </div>
                                                            <span className="font-mono text-[10px] text-slate-500 tnum">
                                                                {Number(exp.correspondence_score).toFixed(2).replace(".", ",")}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    <p className="text-[13px] leading-5 text-slate-700 m-0">{exp.erklaerungstext}</p>

                                                    <div className="flex items-center justify-between gap-2 flex-wrap mt-2">
                                                        <div className="flex items-center gap-1 flex-wrap">
                                                            {(exp.matched_topics || []).map((topic) => (
                                                                <span key={topic} className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                                                                    {topic}
                                                                </span>
                                                            ))}
                                                        </div>
                                                        {exp.quelle?.url && (
                                                            <a
                                                                href={exp.quelle.url}
                                                                target="_blank"
                                                                rel="noreferrer"
                                                                onClick={(e) => e.stopPropagation()}
                                                                className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-700"
                                                            >
                                                                Quelle öffnen
                                                                <ExternalLink className="w-3 h-3" />
                                                            </a>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>

            <p className="text-[11px] text-slate-400 text-center py-2.5 border-t border-slate-100 m-0">
                Erklärungsansätze sind Plausibilisierungen über zeitliche und thematische Korrespondenz — keine Kausalaussagen
            </p>
        </div>
    )
})
