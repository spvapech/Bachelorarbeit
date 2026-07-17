import * as React from "react"
import { useState, useEffect, useMemo, memo, useCallback } from "react"
import {
    ComposedChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts"
import { TrendingUp, RefreshCw, BarChart2 } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogTitle,
} from "@/components/ui/dialog"
import { API_URL } from "@/config"
import { ChartCardHeader, DropdownPicker } from "./ChartHeader"

const MONTH_NAMES = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

function periodLabel(period) {
    const [y, m] = String(period).split("-").map(Number)
    if (!Number.isFinite(y) || !Number.isFinite(m)) return period
    return `${MONTH_NAMES[m - 1]} ${y}`
}

function periodIndex(period) {
    const [y, m] = String(period).split("-").map(Number)
    return y * 12 + (m - 1)
}

const CURRENCY_SYMBOL = { EUR: "€", USD: "$", GBP: "£" }

/* ============================================================================
   StockChartCard — Aktienkursverlauf (Yahoo Finance, persistiert) mit
   optionalem Overlay der Ø-Bewertung und markierten Anomalie-Monaten.
   Ohne hinterlegten Ticker: Einrichtungs-Dialog mit Vorschlagsliste.
   ============================================================================ */
export const StockChartCard = memo(function StockChartCard({ companyId, globalTimeRange = "all" }) {
    const [stock, setStock] = useState(null)          // {ticker, currency, monthly: [...]}
    const [rating, setRating] = useState([])          // [{date "YYYY-MM", score}]
    const [anomalies, setAnomalies] = useState([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [error, setError] = useState(null)
    const [overlay, setOverlay] = useState("Kurs + Rating")
    const [modalOpen, setModalOpen] = useState(false)

    // Ticker-Einrichtung
    const [tickerInput, setTickerInput] = useState("")
    const [suggestions, setSuggestions] = useState([])
    const [saving, setSaving] = useState(false)
    const [refreshErrors, setRefreshErrors] = useState([])

    const fetchAll = useCallback(async () => {
        if (!companyId) return
        try {
            setError(null)
            const [stockRes, timelineRes, anomalyRes] = await Promise.all([
                fetch(`${API_URL}/context/company/${companyId}/stock`),
                fetch(`${API_URL}/analytics/company/${companyId}/timeline?days=3650&forecast_months=0&source=employee`),
                fetch(`${API_URL}/anomalies/company/${companyId}?source=employee&dimension=durchschnittsbewertung`),
            ])
            if (!stockRes.ok) throw new Error(`API Error (stock): ${stockRes.status}`)
            setStock(await stockRes.json())
            if (timelineRes.ok) {
                const t = await timelineRes.json()
                setRating(t.timeline || [])
            }
            if (anomalyRes.ok) {
                const a = await anomalyRes.json()
                setAnomalies(a.anomalies || [])
            }
        } catch (e) {
            console.error("Error fetching stock data:", e)
            setError(e.message)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }, [companyId])

    useEffect(() => {
        if (!companyId) { setLoading(false); return }
        setLoading(true)
        fetchAll()
    }, [companyId, fetchAll])

    // Ticker-Vorschläge (statische DAX/MDAX-Liste im Backend)
    useEffect(() => {
        if (!tickerInput || tickerInput.length < 2) { setSuggestions([]); return }
        const handle = setTimeout(async () => {
            try {
                const res = await fetch(`${API_URL}/context/ticker-suggestions?q=${encodeURIComponent(tickerInput)}`)
                if (res.ok) setSuggestions((await res.json()).suggestions || [])
            } catch { setSuggestions([]) }
        }, 200)
        return () => clearTimeout(handle)
    }, [tickerInput])

    const saveTickerAndLoad = async (ticker) => {
        if (!ticker?.trim()) return
        setSaving(true)
        setRefreshErrors([])
        try {
            const put = await fetch(`${API_URL}/context/company/${companyId}/ticker`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ticker: ticker.trim() }),
            })
            if (!put.ok) throw new Error(`Ticker konnte nicht gespeichert werden (${put.status})`)
            const refresh = await fetch(
                `${API_URL}/context/company/${companyId}/refresh?sources=prices,kpis,news,recommendations`,
                { method: "POST" }
            )
            if (refresh.ok) {
                const result = await refresh.json()
                setRefreshErrors(result.errors || [])
            } else {
                const detail = (await refresh.json().catch(() => ({})))?.detail
                setRefreshErrors([detail || `Refresh fehlgeschlagen (${refresh.status})`])
            }
            await fetchAll()
        } catch (e) {
            setRefreshErrors([e.message])
        } finally {
            setSaving(false)
        }
    }

    const refreshData = async () => {
        setRefreshing(true)
        setRefreshErrors([])
        try {
            const res = await fetch(
                `${API_URL}/context/company/${companyId}/refresh?sources=prices,kpis,news,recommendations`,
                { method: "POST" }
            )
            if (res.ok) setRefreshErrors((await res.json()).errors || [])
            else {
                const detail = (await res.json().catch(() => ({})))?.detail
                setRefreshErrors([detail || `Refresh fehlgeschlagen (${res.status})`])
            }
        } catch (e) {
            setRefreshErrors([e.message])
        }
        await fetchAll()
    }

    // Kurs- und Rating-Monate zusammenführen (Union, chronologisch)
    const chartData = useMemo(() => {
        const stockByPeriod = new Map((stock?.monthly || []).map((m) => [m.period, m.close]))
        const ratingByPeriod = new Map(rating.map((r) => [r.date, r.score]))
        let periods = Array.from(new Set([...stockByPeriod.keys(), ...ratingByPeriod.keys()]))
            .filter((p) => /^\d{4}-\d{2}$/.test(String(p)))
            .sort((a, b) => periodIndex(a) - periodIndex(b))

        if (globalTimeRange !== "all" && periods.length > 0) {
            const months = globalTimeRange === "1y" ? 12 : 36
            const cutoff = periodIndex(periods[periods.length - 1]) - months
            periods = periods.filter((p) => periodIndex(p) >= cutoff)
        }

        return periods.map((p) => ({
            period: p,
            date: periodLabel(p),
            close: stockByPeriod.get(p) ?? null,
            score: ratingByPeriod.get(p) ?? null,
        }))
    }, [stock, rating, globalTimeRange])

    const anomalyDates = useMemo(() => {
        const inRange = new Set(chartData.map((d) => d.period))
        return anomalies
            .filter((a) => inRange.has(a.period))
            .map((a) => ({ date: periodLabel(a.period), direction: a.direction, id: a.id }))
    }, [anomalies, chartData])

    const currency = CURRENCY_SYMBOL[stock?.currency] || stock?.currency || ""
    const hasTicker = Boolean(stock?.ticker)
    const hasPrices = (stock?.monthly || []).length > 0
    const showRating = overlay === "Kurs + Rating"

    const CustomTooltip = ({ active, payload, label }) => {
        if (!active || !payload?.length) return null
        const point = payload[0]?.payload
        return (
            <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[150px]">
                <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{label}</p>
                {point?.close != null && (
                    <p className="flex items-center justify-between gap-3">
                        <span className="inline-flex items-center gap-1.5 text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                            Kurs
                        </span>
                        <span className="font-semibold tnum text-violet-300">
                            {Number(point.close).toFixed(2).replace(".", ",")} {currency}
                        </span>
                    </p>
                )}
                {showRating && point?.score != null && (
                    <p className="flex items-center justify-between gap-3 mt-1">
                        <span className="inline-flex items-center gap-1.5 text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                            Ø Bewertung
                        </span>
                        <span className="font-semibold tnum text-white">
                            {Number(point.score).toFixed(2).replace(".", ",")}
                        </span>
                    </p>
                )}
            </div>
        )
    }

    const StockChart = ({ height = 220 }) => (
        <ResponsiveContainer width="100%" height={height === "100%" ? "100%" : height}>
            <ComposedChart data={chartData} margin={{ left: 0, right: 8, top: 8, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="#f1f5f9" vertical={false} />
                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e2e8f0" }}
                    interval="preserveStartEnd"
                    tickMargin={8}
                />
                <YAxis
                    yAxisId="price"
                    orientation="right"
                    tick={{ fontSize: 10, fill: "#a78bfa" }}
                    tickLine={false}
                    axisLine={false}
                    width={44}
                    domain={["auto", "auto"]}
                    tickFormatter={(v) => `${Math.round(v)} ${currency}`}
                />
                {showRating && (
                    <YAxis
                        yAxisId="rating"
                        orientation="left"
                        domain={[0, 5]}
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        tickLine={false}
                        axisLine={false}
                        width={28}
                        tickFormatter={(v) => v.toFixed(1)}
                    />
                )}
                <Tooltip
                    content={<CustomTooltip />}
                    cursor={{ stroke: "#cbd5e1", strokeWidth: 1, strokeDasharray: "3 3" }}
                />

                {/* Anomalie-Monate als vertikale Markierungen */}
                {anomalyDates.map((a) => (
                    <ReferenceLine
                        key={`stock-anomaly-${a.id ?? a.date}`}
                        yAxisId="price"
                        x={a.date}
                        stroke={a.direction === "fall" ? "#f43f5e" : "#10b981"}
                        strokeDasharray="3 3"
                        strokeOpacity={0.6}
                        strokeWidth={1.5}
                    />
                ))}

                <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="close"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: "#8b5cf6", stroke: "#fff", strokeWidth: 2 }}
                    name="Kurs"
                    connectNulls
                />
                {showRating && (
                    <Line
                        yAxisId="rating"
                        type="monotone"
                        dataKey="score"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4, fill: "#3b82f6", stroke: "#fff", strokeWidth: 2 }}
                        name="Ø Bewertung"
                        connectNulls
                    />
                )}
            </ComposedChart>
        </ResponsiveContainer>
    )

    const ChartLegend = () => (
        <div className="mt-3 flex items-center justify-center gap-4 flex-wrap text-[11px]">
            <div className="flex items-center gap-1.5">
                <div className="h-0.5 w-5 rounded-full bg-violet-500"></div>
                <span className="text-slate-600">Aktienkurs{stock?.ticker ? ` (${stock.ticker})` : ""}</span>
            </div>
            {showRating && (
                <div className="flex items-center gap-1.5">
                    <div className="h-0.5 w-5 rounded-full bg-blue-500"></div>
                    <span className="text-slate-600">Ø Bewertung</span>
                </div>
            )}
            {anomalyDates.length > 0 && (
                <div className="flex items-center gap-1.5">
                    <div className="h-4 w-px" style={{ borderLeft: "2px dashed #f43f5e" }}></div>
                    <span className="text-slate-600">Anomalie-Monat</span>
                </div>
            )}
        </div>
    )

    // Einrichtungs-Ansicht ohne Ticker bzw. ohne Kursdaten
    const SetupView = () => (
        <div className="h-full flex flex-col items-center justify-center gap-3 px-6 text-center" onClick={(e) => e.stopPropagation()}>
            {!hasTicker ? (
                <>
                    <p className="text-[13px] text-slate-600 m-0">
                        Kein Ticker hinterlegt. Yahoo-Finance-Ticker eintragen (z.&nbsp;B. <span className="font-mono">SAP.DE</span>),
                        um Kurse, Kennzahlen und Nachrichten zu laden.
                    </p>
                    <div className="relative w-full max-w-[260px]">
                        <input
                            value={tickerInput}
                            onChange={(e) => setTickerInput(e.target.value)}
                            placeholder="Firmenname oder Ticker suchen…"
                            className="w-full h-8 px-2.5 text-[13px] border border-slate-300 rounded-md bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-300"
                        />
                        {suggestions.length > 0 && (
                            <div className="absolute z-10 top-9 left-0 right-0 bg-white border border-slate-200 rounded-md shadow-md overflow-hidden">
                                {suggestions.slice(0, 6).map((s) => (
                                    <button
                                        key={s.ticker}
                                        className="w-full px-2.5 py-1.5 text-left text-[12px] hover:bg-slate-50 flex justify-between gap-2"
                                        onClick={() => { setTickerInput(s.ticker); setSuggestions([]) }}
                                    >
                                        <span className="text-slate-700 truncate">{s.name}</span>
                                        <span className="font-mono text-slate-500">{s.ticker}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                    <button
                        onClick={() => saveTickerAndLoad(tickerInput)}
                        disabled={saving || !tickerInput.trim()}
                        className="h-8 px-3 rounded-md text-[12px] font-medium bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50 inline-flex items-center gap-1.5"
                    >
                        {saving && <span className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-violet-200 border-t-white" />}
                        {saving ? "Lade Daten…" : "Speichern & Daten laden"}
                    </button>
                </>
            ) : (
                <>
                    <p className="text-[13px] text-slate-600 m-0">
                        Ticker <span className="font-mono">{stock.ticker}</span> hinterlegt, aber noch keine Kursdaten persistiert.
                    </p>
                    <button
                        onClick={refreshData}
                        disabled={refreshing}
                        className="h-8 px-3 rounded-md text-[12px] font-medium bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50 inline-flex items-center gap-1.5"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                        Daten laden (Yahoo Finance)
                    </button>
                </>
            )}
            {refreshErrors.length > 0 && (
                <p className="text-[11px] text-amber-600 m-0 max-w-[320px]">
                    {refreshErrors.join(" · ")}
                </p>
            )}
        </div>
    )

    const emptyMessage = !companyId ? "Keine Firma ausgewählt" : error ? `Fehler: ${error}` : null
    const showSetup = companyId && !error && (!hasTicker || !hasPrices)

    const cardBody = (height) => (
        <>
            {emptyMessage ? (
                <div className="h-full flex items-center justify-center">
                    <p className="text-[13px] text-slate-500">{emptyMessage}</p>
                </div>
            ) : showSetup ? (
                <SetupView />
            ) : (
                <StockChart height={height} />
            )}
            {(loading || refreshing) && (
                <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
                    <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                        <p className="text-slate-600 text-[12px]">{refreshing ? "Aktualisiere Kursdaten…" : "Lade Kursdaten…"}</p>
                    </div>
                </div>
            )}
        </>
    )

    return (
        <>
            <div
                className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer flex flex-col h-full"
                onClick={() => setModalOpen(true)}
            >
                <ChartCardHeader
                    icon={<TrendingUp />}
                    eyebrow="FINANZMARKT · AKTIENKURS"
                    title="Aktienkursverlauf"
                    subtitle={hasTicker ? `${stock.ticker} · Yahoo Finance` : "Ticker einrichten"}
                    expandable
                    actions={hasPrices ? (
                        <>
                            <DropdownPicker
                                label="Ansicht"
                                value={overlay}
                                icon={<BarChart2 />}
                                compact
                                options={[
                                    { value: "Kurs + Rating", label: "Kurs + Rating" },
                                    { value: "Nur Kurs", label: "Nur Kurs" },
                                ]}
                                onChange={setOverlay}
                            />
                            <button
                                title="Daten neu laden (Yahoo Finance)"
                                onClick={(e) => { e.stopPropagation(); refreshData() }}
                                className="h-7 w-7 inline-flex items-center justify-center rounded-md bg-white text-slate-500 border border-slate-300 hover:bg-slate-50 hover:text-slate-700 transition-colors"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                            </button>
                        </>
                    ) : null}
                />

                <div className="px-4 pt-4 pb-4 flex flex-col flex-1 min-h-0">
                    <div className="relative h-[220px] w-full flex-shrink-0">
                        {cardBody(220)}
                    </div>
                    {hasPrices && !showSetup && <ChartLegend />}
                    {refreshErrors.length > 0 && hasPrices && (
                        <p className="text-[11px] text-amber-600 text-center mt-2 m-0">{refreshErrors.join(" · ")}</p>
                    )}
                    <div className="flex-1" />
                    <p className="text-[11px] text-slate-400 text-center mt-3">
                        {hasPrices ? "Karte anklicken zum Vergrössern" : "Persistierte Daten · kein Live-Abruf"}
                    </p>
                </div>
            </div>

            <Dialog open={modalOpen} onOpenChange={setModalOpen}>
                <DialogContent
                    className="overflow-hidden flex flex-col p-0 gap-0"
                    style={{ width: "90vw", maxWidth: "90vw", height: "85vh", maxHeight: "85vh" }}
                >
                    <span aria-hidden="true" className="block h-[3px] w-full bg-violet-500" />
                    <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start justify-between gap-3 flex-shrink-0">
                        <div className="flex items-start gap-2.5">
                            <span className="w-9 h-9 rounded-md grid place-items-center bg-violet-50 text-violet-600 flex-none">
                                <TrendingUp className="w-[18px] h-[18px]" />
                            </span>
                            <div>
                                <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                                    FINANZMARKT · AKTIENKURS
                                </p>
                                <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900">
                                    Aktienkursverlauf
                                </DialogTitle>
                                <p className="m-0 mt-0.5 text-[11px] text-slate-500">
                                    {hasTicker ? `${stock.ticker} · Yahoo Finance` : "Ticker einrichten"}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex-1 flex flex-col min-h-0 px-5 py-4">
                        <div className="flex-1 min-h-0 relative overflow-hidden">
                            {cardBody("100%")}
                        </div>
                        {hasPrices && !showSetup && <ChartLegend />}
                    </div>
                </DialogContent>
            </Dialog>
        </>
    )
})
