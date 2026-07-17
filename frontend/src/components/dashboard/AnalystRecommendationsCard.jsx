import * as React from "react"
import { useState, useEffect, useMemo, useCallback, memo } from "react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"
import { ThumbsUp, RefreshCw } from "lucide-react"
import { API_URL } from "@/config"
import { ChartCardHeader } from "./ChartHeader"

const MONTH_NAMES = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

function monthLabel(month) {
    const [y, m] = String(month).split("-").map(Number)
    if (!Number.isFinite(y) || !Number.isFinite(m)) return month
    return `${MONTH_NAMES[m - 1]} ${y}`
}

/* Kategorien in Stapel-Reihenfolge (unten → oben), Farben im Yahoo-Finance-Stil */
const CATEGORIES = [
    { key: "strong_buy", label: "Strong Buy", color: "#15803d" },
    { key: "buy", label: "Buy", color: "#22c55e" },
    { key: "hold", label: "Hold", color: "#facc15" },
    { key: "sell", label: "Underperform", color: "#fb923c" },
    { key: "strong_sell", label: "Sell", color: "#ef4444" },
]

/* Segment-Beschriftung nur bei ausreichend großen Segmenten (sonst unleserlich).
   Bei gestapelten Bars kann `value` als [start, ende] ankommen. */
const SegmentLabel = ({ x, y, width, height, value }) => {
    const count = Array.isArray(value) ? value[value.length - 1] - value[0] : value
    if (!count || height < 14) return null
    return (
        <text
            x={x + width / 2}
            y={y + height / 2}
            fill="#fff"
            fontSize={11}
            fontWeight={600}
            textAnchor="middle"
            dominantBaseline="central"
        >
            {count}
        </text>
    )
}

/* ============================================================================
   AnalystRecommendationsCard — monatliche Verteilung der Analystenempfehlungen
   (Yahoo Finance, persistiert) als gestapeltes Balkendiagramm.
   ============================================================================ */
export const AnalystRecommendationsCard = memo(function AnalystRecommendationsCard({ companyId }) {
    const [rows, setRows] = useState([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [error, setError] = useState(null)

    const fetchData = useCallback(async () => {
        if (!companyId) return
        try {
            setError(null)
            const res = await fetch(`${API_URL}/context/company/${companyId}/recommendations`)
            if (!res.ok) throw new Error(`API Error (recommendations): ${res.status}`)
            const json = await res.json()
            setRows(json.recommendations || [])
        } catch (e) {
            console.error("Error fetching analyst recommendations:", e)
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }, [companyId])

    useEffect(() => {
        if (!companyId) { setLoading(false); setRows([]); return }
        setLoading(true)
        fetchData()
    }, [companyId, fetchData])

    const refresh = async (e) => {
        e?.stopPropagation()
        if (!companyId) return
        setRefreshing(true)
        try {
            await fetch(`${API_URL}/context/company/${companyId}/refresh?sources=recommendations`, { method: "POST" })
            await fetchData()
        } catch (err) {
            console.error("Error refreshing recommendations:", err)
        } finally {
            setRefreshing(false)
        }
    }

    // Letzte 6 Monate, chronologisch; Gesamtzahl je Monat für die Kopfzeile
    const chartData = useMemo(() => (
        rows.slice(-6).map((r) => ({
            month: monthLabel(r.month),
            strong_buy: r.strong_buy || 0,
            buy: r.buy || 0,
            hold: r.hold || 0,
            sell: r.sell || 0,
            strong_sell: r.strong_sell || 0,
            total: CATEGORIES.reduce((s, c) => s + (r[c.key] || 0), 0),
        }))
    ), [rows])

    const latestTotal = chartData.length ? chartData[chartData.length - 1].total : null

    const CustomTooltip = ({ active, payload, label }) => {
        if (!active || !payload?.length) return null
        const point = payload[0]?.payload
        return (
            <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[160px]">
                <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{label}</p>
                {CATEGORIES.map((cat) => (
                    <p key={cat.key} className="flex items-center justify-between gap-3 mt-0.5">
                        <span className="inline-flex items-center gap-1.5 text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full" style={{ background: cat.color }} />
                            {cat.label}
                        </span>
                        <span className="font-semibold tnum text-white">{point?.[cat.key] ?? 0}</span>
                    </p>
                ))}
                <p className="text-slate-500 mt-1.5 pt-1.5 border-t border-slate-700 tnum text-[11px]">
                    {point?.total} Analysten
                </p>
            </div>
        )
    }

    const emptyMessage =
        !companyId ? "Keine Firma ausgewählt"
        : error ? `Fehler: ${error}`
        : chartData.length === 0
            ? "Keine Empfehlungen persistiert — Ticker einrichten und Daten laden (Aktienkurs-Karte)"
            : null

    return (
        <div className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow flex flex-col h-full">
            <ChartCardHeader
                icon={<ThumbsUp />}
                eyebrow="FINANZMARKT · ANALYSTENEMPFEHLUNGEN"
                title="Analyst Recommendations"
                subtitle={latestTotal ? `${latestTotal} Analysten · Yahoo Finance` : "Verteilung je Monat"}
                actions={chartData.length > 0 ? (
                    <button
                        title="Empfehlungen neu laden (Yahoo Finance)"
                        onClick={refresh}
                        className="h-7 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-white text-slate-600 border border-slate-300 hover:bg-slate-50 transition-colors"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                        Aktualisieren
                    </button>
                ) : null}
            />

            <div className="px-4 pt-4 pb-4 flex flex-col flex-1 min-h-0">
                <div className="relative h-[240px] w-full flex-shrink-0">
                    {emptyMessage && !loading ? (
                        <div className="h-full flex items-center justify-center px-6">
                            <p className="text-[13px] text-slate-500 text-center max-w-[280px] m-0">{emptyMessage}</p>
                        </div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} margin={{ left: 0, right: 8, top: 8, bottom: 5 }} barCategoryGap="28%">
                                <CartesianGrid strokeDasharray="2 4" stroke="#f1f5f9" vertical={false} />
                                <XAxis
                                    dataKey="month"
                                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                                    tickLine={false}
                                    axisLine={{ stroke: "#e2e8f0" }}
                                    tickMargin={8}
                                />
                                <YAxis
                                    allowDecimals={false}
                                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                                    tickLine={false}
                                    axisLine={false}
                                    width={28}
                                />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148, 163, 184, 0.08)" }} />
                                {CATEGORIES.map((cat) => (
                                    <Bar
                                        key={cat.key}
                                        dataKey={cat.key}
                                        stackId="empfehlungen"
                                        fill={cat.color}
                                        name={cat.label}
                                        isAnimationActive={false}
                                        label={<SegmentLabel />}
                                    />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                    {(loading || refreshing) && (
                        <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
                            <div className="flex items-center gap-2">
                                <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                                <p className="text-slate-600 text-[12px] m-0">Lade Empfehlungen…</p>
                            </div>
                        </div>
                    )}
                </div>

                <div className="mt-3 flex items-center justify-center gap-3 flex-wrap text-[11px]">
                    {CATEGORIES.map((cat) => (
                        <div key={cat.key} className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: cat.color }}></span>
                            <span className="text-slate-600">{cat.label}</span>
                        </div>
                    ))}
                </div>

                <div className="flex-1" />
                <p className="text-[11px] text-slate-400 text-center mt-3 m-0">
                    Yahoo Finance (persistiert) · wiederholte Abrufe bauen Historie auf
                </p>
            </div>
        </div>
    )
})
