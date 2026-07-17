import * as React from "react"
import {
    AreaChart,
    Area,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    ReferenceDot,
    Legend,
    ComposedChart,
} from "recharts"
import { Filter, ChevronDown, Maximize2, X, Activity, BarChart2, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useState, useEffect, useMemo, useCallback, memo } from "react"
import { API_URL } from "@/config"
import { ChartCardHeader, SourceToggle, DropdownPicker } from "./ChartHeader"
import { TrendUp as TrendUpIcon } from "../../icons"

const SOURCE_LABEL = {
    employee: "Mitarbeiter",
    candidates: "Bewerber",
}

const GRANULARITY_LABEL = {
    overall: "ges. Zeitraum",
    year: "Jahr",
}

function parseYear(period) {
    if (!period) return null
    const y = Number(String(period).slice(0, 4))
    return Number.isFinite(y) ? y : null
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

// Fill in missing months and create gap bridge data for dashed line display (valueKey: 'score' or 'count')
function processTimelineDataWithGaps(timelineData, valueKey) {
    if (!timelineData?.length || timelineData.length < 2) return { data: [], hasGaps: false }

    const validData = timelineData
        .map((d) => {
            const dateStr = d.date
            if (!dateStr || typeof dateStr !== 'string') return null
            const [y, m] = dateStr.split('-').map(Number)
            if (!Number.isFinite(y) || !Number.isFinite(m)) return null
            return {
                year: y,
                monthNum: m,
                date: `${MONTH_NAMES[m - 1]} ${y}`,
                [valueKey]: valueKey === 'score' ? d.score : d.count,
                count: d.count,
                score: d.score,
            }
        })
        .filter((d) => d != null && d[valueKey] != null)

    if (validData.length < 2) return { data: [], hasGaps: false }

    const sorted = [...validData].sort((a, b) => {
        if (a.year !== b.year) return a.year - b.year
        return a.monthNum - b.monthNum
    })

    const dataMap = new Map()
    sorted.forEach((item) => {
        dataMap.set(`${item.year}-${item.monthNum}`, item)
    })

    const result = []
    let hasGaps = false
    const first = sorted[0]
    const last = sorted[sorted.length - 1]
    let y = first.year
    let m = first.monthNum

    while (y < last.year || (y === last.year && m <= last.monthNum)) {
        const existing = dataMap.get(`${y}-${m}`)
        const gapKey = valueKey + 'Gap'
        if (existing) {
            result.push({ ...existing, [gapKey]: null, _isMissing: false })
        } else {
            hasGaps = true
            result.push({
                date: `${MONTH_NAMES[m - 1]} ${y}`,
                year: y,
                monthNum: m,
                [valueKey]: null,
                [gapKey]: null,
                count: null,
                _isMissing: true,
            })
        }
        m++
        if (m > 12) {
            m = 1
            y++
        }
    }

    let i = 0
    const gapKey = valueKey + 'Gap'
    while (i < result.length) {
        if (!result[i]._isMissing) {
            i++
            continue
        }
        const gapStart = i
        let gapEnd = i
        while (gapEnd < result.length && result[gapEnd]._isMissing) gapEnd++
        const beforeIdx = gapStart - 1
        const afterIdx = gapEnd
        if (
            beforeIdx >= 0 &&
            afterIdx < result.length &&
            result[beforeIdx][valueKey] != null &&
            result[afterIdx][valueKey] != null
        ) {
            const beforeVal = result[beforeIdx][valueKey]
            const afterVal = result[afterIdx][valueKey]
            const totalLen = afterIdx - beforeIdx
            result[beforeIdx][gapKey] = beforeVal
            result[afterIdx][gapKey] = afterVal
            for (let j = gapStart; j < gapEnd; j++) {
                const t = (j - beforeIdx) / totalLen
                const interp = valueKey === 'count' ? Math.round(beforeVal + t * (afterVal - beforeVal)) : +(beforeVal + t * (afterVal - beforeVal)).toFixed(2)
                result[j][gapKey] = interp
            }
        }
        i = gapEnd
    }

    return { data: result, hasGaps }
}

// Memoized TimelineCard für bessere Performance
export const TimelineCard = memo(function TimelineCard({ companyId, onFiltersChange, onLoadingChange, globalTimeRange = "all" }) {
    const [timelineData, setTimelineData] = useState([])
    const [forecastData, setForecastData] = useState([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [error, setError] = useState(null)
    const [metric, setMetric] = useState("Ø Score")
    const [source, setSource] = useState("employee")
    const [granularity, setGranularity] = useState("overall")
    const [selectedYear, setSelectedYear] = useState(null)
    const [years, setYears] = useState([])
    const [modalOpen, setModalOpen] = useState(false)
    const [anomalies, setAnomalies] = useState([])
    
    // Kommuniziere Loading-State nach außen
    useEffect(() => {
        if (onLoadingChange) {
            onLoadingChange(loading);
        }
    }, [loading, onLoadingChange]);

    // Fetch available years from timeline data
    useEffect(() => {
        if (!companyId) return

        const fetchYears = async () => {
            try {
                // Fetch with large days to get all available data to extract years
                const response = await fetch(
                    `${API_URL}/analytics/company/${companyId}/timeline?days=3650&forecast_months=0&source=${source}`
                )
                if (!response.ok) throw new Error(`API Error (years): ${response.status}`)
                const json = await response.json()

                const ys = (json.timeline || [])
                    .map((d) => parseYear(d.date))
                    .filter((y) => y !== null)

                const uniq = Array.from(new Set(ys)).sort((a, b) => a - b)
                setYears(uniq)

                if (granularity === "year") {
                    const newest = uniq.length ? uniq[uniq.length - 1] : null
                    setSelectedYear((prev) => {
                        if (prev == null) return newest
                        if (uniq.includes(prev)) return prev
                        return newest
                    })
                }
            } catch (e) {
                console.error("Error fetching years:", e)
                setYears([])
            }
        }

        fetchYears()
    }, [companyId, granularity, source])

    useEffect(() => {
        if (!companyId) return

        const fetchTimelineData = async () => {
            // First load → full loading screen; subsequent refetches → silent overlay
            const isFirst = timelineData.length === 0
            isFirst ? setLoading(true) : setRefreshing(true)
            try {
                setError(null)

                // Calculate days based on granularity and global time range
                let days = globalTimeRange === "1y" ? 365 : globalTimeRange === "3y" ? 1095 : 3650

                if (granularity === "year") {
                    if (selectedYear) {
                        const now = new Date()
                        const yearStart = new Date(selectedYear, 0, 1)
                        const daysToYearStart = Math.ceil((now - yearStart) / (1000 * 60 * 60 * 24))
                        days = daysToYearStart + 400
                    } else {
                        setTimelineData([])
                        setForecastData([])
                        setLoading(false)
                        setRefreshing(false)
                        return
                    }
                }

                const response = await fetch(
                    `${API_URL}/analytics/company/${companyId}/timeline?days=${days}&forecast_months=6&source=${source}`
                )

                if (!response.ok) {
                    throw new Error(`API Error: ${response.status}`)
                }

                const data = await response.json()

                let filteredTimeline = data.timeline || []
                if (granularity === "year" && selectedYear) {
                    filteredTimeline = filteredTimeline.filter((item) => {
                        const itemYear = parseYear(item.date)
                        return itemYear === selectedYear
                    })
                }

                setTimelineData(filteredTimeline)
                setForecastData(data.forecast || [])
            } catch (err) {
                console.error('Error fetching timeline data:', err)
                setError(err.message)
            } finally {
                setLoading(false)
                setRefreshing(false)
            }
        }

        fetchTimelineData()
    }, [companyId, granularity, selectedYear, source, globalTimeRange])

    // Anomalien (2. Design-Zyklus): erkannte Extremveränderungen der Ø-Bewertung.
    // Der Endpoint führt beim ersten Aufruf automatisch eine Default-Erkennung aus.
    useEffect(() => {
        if (!companyId) { setAnomalies([]); return }
        let cancelled = false
        const fetchAnomalies = async () => {
            try {
                const response = await fetch(
                    `${API_URL}/anomalies/company/${companyId}?source=${source}&dimension=durchschnittsbewertung`
                )
                if (!response.ok) throw new Error(`API Error (anomalies): ${response.status}`)
                const json = await response.json()
                if (!cancelled) setAnomalies(json.anomalies || [])
            } catch (e) {
                console.error("Error fetching anomalies:", e)
                if (!cancelled) setAnomalies([])
            }
        }
        fetchAnomalies()
        return () => { cancelled = true }
    }, [companyId, source])

    // Calculate trend (delta) for each month compared to previous month
    const trendData = useMemo(() => {
        if (timelineData.length < 2 || metric !== "Trend") return []
        
        const trends = []
        for (let i = 0; i < timelineData.length; i++) {
            if (i === 0) {
                // First month: no previous month to compare, set to 0 or null
                trends.push({
                    date: timelineData[i].date_display || timelineData[i].date,
                    trend: 0,
                    score: timelineData[i].score,
                    prevScore: null
                })
            } else {
                const current = timelineData[i].score
                const previous = timelineData[i - 1].score
                const delta = current - previous
                trends.push({
                    date: timelineData[i].date_display || timelineData[i].date,
                    trend: delta,
                    score: current,
                    prevScore: previous
                })
            }
        }
        return trends
    }, [timelineData, metric])

    // Calculate forecast trends
    const forecastTrendData = useMemo(() => {
        if (metric !== "Trend" || forecastData.length === 0 || timelineData.length === 0) return []
        
        const forecastTrends = []
        const lastHistoricalScore = timelineData[timelineData.length - 1].score
        
        // First forecast month: trend from last historical to first forecast
        if (forecastData.length > 0) {
            const firstForecastScore = forecastData[0].score
            forecastTrends.push({
                date: forecastData[0].date_display || forecastData[0].date,
                trend: firstForecastScore - lastHistoricalScore,
                score: firstForecastScore,
                prevScore: lastHistoricalScore
            })
        }
        
        // Subsequent forecast months: trend from previous forecast month
        for (let i = 1; i < forecastData.length; i++) {
            const current = forecastData[i].score
            const previous = forecastData[i - 1].score
            forecastTrends.push({
                date: forecastData[i].date_display || forecastData[i].date,
                trend: current - previous,
                score: current,
                prevScore: previous
            })
        }
        
        return forecastTrends
    }, [forecastData, timelineData, metric])

    // Process historical timeline with gap filling (Ø Score and Anzahl only)
    const { data: processedHistorical, hasGaps: timelineHasGaps } = useMemo(() => {
        if (metric !== "Ø Score" && metric !== "Anzahl") return { data: [], hasGaps: false }
        const valueKey = metric === "Anzahl" ? "count" : "score"
        return processTimelineDataWithGaps(timelineData, valueKey)
    }, [timelineData, metric])

    // Prepare chart data - combine historical and forecast with bridge point
    const chartData = useMemo(() => {
        if (timelineData.length === 0) return []

        // For Trend metric, combine historical trends and forecast trends
        if (metric === "Trend") {
            const historicalTrends = trendData.map(item => ({
                date: item.date,
                historical: item.trend,
                forecast: null,
                count: null,
                score: item.score,
                prevScore: item.prevScore
            }))
            
            // Add bridge point: last historical also gets forecast value matching its own trend
            // This ensures the forecast line starts exactly where the historical line ends
            if (historicalTrends.length > 0 && forecastTrendData.length > 0) {
                const lastHistorical = historicalTrends[historicalTrends.length - 1]
                lastHistorical.forecast = lastHistorical.historical
            }
            
            // Add forecast trends - start from the last historical date (skip first forecast point as it's already on the bridge point)
            const forecastTrends = []
            if (forecastTrendData.length > 0 && historicalTrends.length > 0) {
                // First forecast point at last historical date (bridge point - already handled above)
                // Start from second forecast point onwards
                for (let i = 1; i < forecastTrendData.length; i++) {
                    forecastTrends.push({
                        date: forecastTrendData[i].date,
                        historical: null,
                        forecast: forecastTrendData[i].trend,
                        count: null,
                        score: forecastTrendData[i].score,
                        prevScore: forecastTrendData[i].prevScore
                    })
                }
            }
            
            return [...historicalTrends, ...forecastTrends]
        }

        // Historical: use gap-filled data when available (Ø Score / Anzahl with 2+ points)
        const valueKey = metric === "Anzahl" ? "count" : "score"
        const gapKey = valueKey + "Gap"
        let historical
        if (processedHistorical.length > 0) {
            historical = processedHistorical.map((row, index) => {
                const isLast = index === processedHistorical.length - 1
                return {
                    date: row.date,
                    historical: row[valueKey] ?? null,
                    historicalGap: row[gapKey] ?? null,
                    _isMissing: row._isMissing,
                    count: row.count ?? null,
                    score: row.score ?? null,
                    forecast: isLast && forecastData.length > 0 && metric === "Ø Score" ? row[valueKey] : null,
                }
            })
            // Bridge: last historical point gets forecast value for line connection
            if (historical.length > 0 && forecastData.length > 0 && metric === "Ø Score") {
                historical[historical.length - 1].forecast = historical[historical.length - 1].historical
            }
        } else {
            historical = timelineData.map((item, index) => {
                const isLast = index === timelineData.length - 1
                return {
                    date: item.date_display || item.date,
                    historical: metric === "Anzahl" ? item.count : item.score,
                    historicalGap: null,
                    _isMissing: false,
                    forecast: isLast && forecastData.length > 0 && metric === "Ø Score" ? item.score : null,
                    count: item.count,
                    score: item.score,
                }
            })
        }

        // Forecast data points - only show forecast for "Ø Score" mode
        const forecast = metric === "Ø Score" ? forecastData.map(item => ({
            date: item.date_display || item.date,
            historical: null,
            historicalGap: null,
            forecast: item.score,
            count: null,
            score: null,
        })) : []

        return [...historical, ...forecast]
    }, [timelineData, forecastData, metric, trendData, forecastTrendData, processedHistorical])

    // Find the last historical date for reference line — derived from chartData so the
    // format always matches the XAxis dataKey (processTimelineDataWithGaps converts dates
    // from "2024-01" to "Jan 2024", so we cannot use timelineData directly here).
    const lastHistoricalDate = useMemo(() => {
        for (let i = chartData.length - 1; i >= 0; i--) {
            if (chartData[i].historical !== null) return chartData[i].date
        }
        return null
    }, [chartData])

    // Anomalien auf X-Achsen-Labels mappen ("2023-01" → "Jan 2023", wie
    // processTimelineDataWithGaps die Daten formatiert)
    const anomalyByDate = useMemo(() => {
        const map = new Map()
        anomalies.forEach((a) => {
            const [y, m] = String(a.period).split("-").map(Number)
            if (!Number.isFinite(y) || !Number.isFinite(m)) return
            map.set(`${MONTH_NAMES[m - 1]} ${y}`, a)
        })
        return map
    }, [anomalies])

    const anomalyMarks = useMemo(() => {
        if (metric !== "Ø Score") return []
        return chartData
            .filter((row) => row.historical != null && anomalyByDate.has(row.date))
            .map((row) => ({ date: row.date, value: row.historical, anomaly: anomalyByDate.get(row.date) }))
    }, [chartData, anomalyByDate, metric])

    // Calculate Y-axis domain based on metric
    const yAxisDomain = useMemo(() => {
        if (metric === "Anzahl") {
            const maxCount = Math.max(...timelineData.map(item => item.count || 0), 1)
            // Add some padding (20% or at least 1)
            const padding = Math.max(maxCount * 0.2, 1)
            return [0, Math.ceil(maxCount + padding)]
        }
        if (metric === "Trend") {
            // For trend, we need to handle negative values
            const trendValues = trendData.map(item => item.trend)
            const minTrend = Math.min(...trendValues, 0)
            const maxTrend = Math.max(...trendValues, 0)
            const padding = Math.max(Math.abs(minTrend), Math.abs(maxTrend)) * 0.2
            return [Math.floor(minTrend - padding), Math.ceil(maxTrend + padding)]
        }
        return [0, 5] // Default for "Ø Score"
    }, [timelineData, metric, trendData])

    useEffect(() => {
        if (onFiltersChange) {
            let stats = {};
            
            if (timelineData.length > 0) {
                stats.dataPoints = timelineData.length;

                const fmt = (d) => { const dt = new Date(d.date || d.period); return dt.toLocaleDateString('de-DE', { month: 'short', year: 'numeric' }); };
                stats.dateRange = `${fmt(timelineData[0])} – ${fmt(timelineData[timelineData.length - 1])}`;
                if (forecastData.length > 0) {
                    stats.dateRangeSub = `${fmt(timelineData[0])} – ${fmt(forecastData[forecastData.length - 1])}`;
                    stats.forecastRange = `${fmt(forecastData[0])} – ${fmt(forecastData[forecastData.length - 1])}`;
                }

                if (metric === "Anzahl") {
                    const totalCount = timelineData.reduce((sum, d) => sum + (d.count || 0), 0);
                    stats.avgCount = (totalCount / timelineData.length).toFixed(1);
                    stats.maxCount = Math.max(...timelineData.map(d => d.count || 0));
                } else if (metric === "Trend" && trendData.length > 0) {
                    const avgTrend = trendData.length > 1
                        ? (trendData.slice(1).reduce((sum, d) => sum + d.trend, 0) / (trendData.length - 1)).toFixed(2)
                        : "0.00";
                    stats.avgTrend = avgTrend;
                    stats.maxTrend = Math.max(...trendData.map(d => d.trend)).toFixed(2);
                    stats.minTrend = Math.min(...trendData.map(d => d.trend)).toFixed(2);
                } else if (metric === "Ø Score") {
                    stats.avgHistorical = (timelineData.reduce((sum, d) => sum + d.score, 0) / timelineData.length).toFixed(2);
                    if (forecastData.length > 0) {
                        stats.avgForecast = (forecastData.reduce((sum, d) => sum + d.score, 0) / forecastData.length).toFixed(2);
                    }
                }
            }
            
            onFiltersChange({
                metric,
                source,
                granularity,
                selectedYear,
                stats,
                hasForecast: forecastData.length > 0,
                hasInterpolation: processedHistorical.length > 0 && processedHistorical.some(d => d._isMissing),
            });
        }
    }, [metric, source, granularity, selectedYear, timelineData, forecastData, trendData, onFiltersChange]);

    // Custom tooltip — slate-900 dark style mit Mono-Zahlen
    const CustomTooltip = ({ active, payload, label }) => {
        if (!active || !payload?.length) return null
        const historicalValue = payload.find(p => p.dataKey === "historical")?.value
        const forecastValue = payload.find(p => p.dataKey === "forecast")?.value
        const dataPoint = payload[0]?.payload
        const isMissing = dataPoint?._isMissing
        const fmtV = (v) => metric === "Anzahl" ? Math.round(v) : Number(v).toFixed(2).replace(".", ",")

        return (
            <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[140px]">
                <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{label}</p>
                {isMissing ? (
                    <>
                        <p className="text-amber-400 inline-flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                            Interpolierter Wert
                        </p>
                        {dataPoint?.historicalGap != null && (
                            <p className="flex items-center justify-between gap-3 mt-1">
                                <span className="text-slate-400">Wert</span>
                                <span className="font-semibold tnum text-amber-300">{fmtV(dataPoint.historicalGap)}</span>
                            </p>
                        )}
                    </>
                ) : (
                    <>
                        {historicalValue != null && (
                            <p className="flex items-center justify-between gap-3">
                                <span className="inline-flex items-center gap-1.5 text-slate-400">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                                    {metric === "Trend" ? "Trend" : "Historisch"}
                                </span>
                                <span className={`font-semibold tnum ${
                                    metric === "Trend"
                                        ? (historicalValue >= 0 ? "text-emerald-400" : "text-rose-400")
                                        : "text-white"
                                }`}>
                                    {metric === "Trend" && historicalValue >= 0 ? "+" : ""}
                                    {fmtV(historicalValue)}
                                </span>
                            </p>
                        )}
                        {forecastValue != null && (
                            <p className="flex items-center justify-between gap-3 mt-1">
                                <span className="inline-flex items-center gap-1.5 text-slate-400">
                                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                                    Prognose
                                </span>
                                <span className={`font-semibold tnum ${
                                    metric === "Trend"
                                        ? (forecastValue >= 0 ? "text-emerald-400" : "text-rose-400")
                                        : "text-orange-300"
                                }`}>
                                    {metric === "Trend" && forecastValue >= 0 ? "+" : ""}
                                    {fmtV(forecastValue)}
                                </span>
                            </p>
                        )}
                        {metric === "Ø Score" && dataPoint?.count && (
                            <p className="text-slate-500 mt-1.5 pt-1.5 border-t border-slate-700 tnum text-[11px]">
                                {dataPoint.count} {dataPoint.count === 1 ? "Bewertung" : "Bewertungen"}
                            </p>
                        )}
                        {metric === "Ø Score" && anomalyByDate.has(label) && (() => {
                            const anomaly = anomalyByDate.get(label)
                            const isFall = anomaly.direction === "fall"
                            return (
                                <p className="flex items-center justify-between gap-3 mt-1.5 pt-1.5 border-t border-slate-700">
                                    <span className="inline-flex items-center gap-1.5 text-slate-400">
                                        <span className={`w-1.5 h-1.5 rounded-full ${isFall ? "bg-rose-400" : "bg-emerald-400"}`} />
                                        Anomalie ({String(anomaly.method).toUpperCase()})
                                    </span>
                                    <span className={`font-semibold tnum ${isFall ? "text-rose-400" : "text-emerald-400"}`}>
                                        {isFall ? "−" : "+"}{Math.abs(Number(anomaly.magnitude)).toFixed(2).replace(".", ",")}
                                    </span>
                                </p>
                            )
                        })()}
                    </>
                )}
            </div>
        )
    }

    // Filter dropdowns component (reusable)
    // The Timeline shows historical data + forecast — granularity/year picker
    // would be misleading here, so only Source + Metric are exposed.
    const FilterDropdowns = ({ compact = false }) => (
        <>
            <SourceToggle
                value={source}
                onChange={setSource}
                compact={compact}
                options={[
                    { value: "employee",   label: "Mitarbeiter", color: "#3b82f6", icon: true },
                    { value: "candidates", label: "Bewerber",    color: "#10b981", icon: true },
                ]}
            />

            <DropdownPicker
                label="Metrik"
                value={metric}
                icon={<BarChart2 />}
                compact={compact}
                options={[
                    { value: "Ø Score", label: "Ø Score" },
                    { value: "Trend",   label: "Trend" },
                ]}
                onChange={setMetric}
            />
        </>
    )

    // Chart component — Modern Area-Chart mit Gradient-Fill (Stripe/Linear-Stil)
    const TimelineChart = ({ height = 200 }) => (
        <ResponsiveContainer width="100%" height={height === "100%" ? "100%" : height}>
            <ComposedChart
                data={chartData}
                margin={{ left: 0, right: 16, top: 8, bottom: 5 }}
            >
                {/* Gradient-Definitionen für Area-Fills */}
                <defs>
                    <linearGradient id="histGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#3b82f6" stopOpacity={0.18} />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#10b981" stopOpacity={0.18} />
                        <stop offset="100%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#f97316" stopOpacity={0.14} />
                        <stop offset="100%" stopColor="#f97316" stopOpacity={0.0} />
                    </linearGradient>
                </defs>

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
                    domain={yAxisDomain}
                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                    tickLine={false}
                    axisLine={false}
                    width={32}
                    tickFormatter={(value) => {
                        if (metric === "Anzahl") return Math.round(value).toString()
                        if (metric === "Trend") return (value >= 0 ? "+" : "") + value.toFixed(1)
                        return value.toFixed(1)
                    }}
                />
                <Tooltip
                    content={<CustomTooltip />}
                    cursor={{ stroke: "#cbd5e1", strokeWidth: 1, strokeDasharray: "3 3" }}
                />

                {/* Reference line at y=0 für Trend */}
                {metric === "Trend" && (
                    <ReferenceLine y={0} stroke="#cbd5e1" strokeDasharray="2 4" strokeWidth={1} />
                )}

                {/* Trennlinie historisch ↔ forecast */}
                {((metric === "Ø Score" && forecastData.length > 0) ||
                  (metric === "Trend"   && forecastTrendData.length > 0)) && lastHistoricalDate && (
                    <ReferenceLine
                        x={lastHistoricalDate}
                        stroke="#94a3b8"
                        strokeDasharray="3 3"
                        strokeWidth={1.5}
                    />
                )}

                {/* === Historische Daten === */}
                {metric !== "Trend" && (
                    <Area
                        type="monotone"
                        dataKey="historical"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        fill="url(#histGradient)"
                        dot={false}
                        activeDot={{ r: 4, fill: "#3b82f6", stroke: "#fff", strokeWidth: 2 }}
                        name="Historisch"
                        connectNulls={false}
                    />
                )}

                {metric === "Trend" && (
                    <Area
                        type="monotone"
                        dataKey="historical"
                        stroke="#10b981"
                        strokeWidth={2}
                        fill="url(#trendGradient)"
                        dot={false}
                        activeDot={{ r: 4, fill: "#10b981", stroke: "#fff", strokeWidth: 2 }}
                        name="Trend Historisch"
                        connectNulls={false}
                    />
                )}

                {/* Gestrichelte Gap-Line bei Lücken — deutlich sichtbar über der Area */}
                {metric !== "Trend" && timelineHasGaps && (
                    <Line
                        type="monotone"
                        dataKey="historicalGap"
                        stroke="#94a3b8"
                        strokeWidth={2}
                        strokeDasharray="6 4"
                        strokeOpacity={0.85}
                        dot={false}
                        activeDot={false}
                        connectNulls={false}
                        legendType="none"
                        isAnimationActive={false}
                    />
                )}

                {/* === Forecast === */}
                {metric === "Ø Score" && (
                    <Area
                        type="monotone"
                        dataKey="forecast"
                        stroke="#f97316"
                        strokeWidth={2}
                        strokeDasharray="5 3"
                        fill="url(#forecastGradient)"
                        dot={false}
                        activeDot={{ r: 4, fill: "#f97316", stroke: "#fff", strokeWidth: 2 }}
                        name="Prognose"
                        connectNulls={false}
                    />
                )}

                {metric === "Trend" && forecastTrendData.length > 0 && (
                    <Area
                        type="monotone"
                        dataKey="forecast"
                        stroke="#f97316"
                        strokeWidth={2}
                        strokeDasharray="5 3"
                        fill="url(#forecastGradient)"
                        dot={false}
                        activeDot={{ r: 4, fill: "#f97316", stroke: "#fff", strokeWidth: 2 }}
                        name="Trend Prognose"
                        connectNulls={false}
                    />
                )}

                {/* === Anomalie-Marker (2. Design-Zyklus) === */}
                {metric === "Ø Score" && anomalyMarks.map((mark) => (
                    <ReferenceDot
                        key={`anomaly-${mark.anomaly.id ?? mark.date}`}
                        x={mark.date}
                        y={mark.value}
                        r={5}
                        fill={mark.anomaly.direction === "fall" ? "#f43f5e" : "#10b981"}
                        stroke="#fff"
                        strokeWidth={2}
                        isFront
                    />
                ))}
            </ComposedChart>
        </ResponsiveContainer>
    )

    // Legend component (reusable)
    const ChartLegend = ({ compact = false }) => (
        <div className={`${compact ? 'mt-2' : 'mt-3'} flex items-center justify-center gap-4 flex-wrap text-[11px]`}>
            <div className="flex items-center gap-1.5">
                <div className="h-0.5 w-5 rounded-full bg-blue-500"></div>
                <span className="text-slate-600">Historisch</span>
            </div>
            {metric === "Trend" && (
                <>
                    <div className="flex items-center gap-2">
                        <div className="h-1 w-6 rounded-full bg-green-500"></div>
                        <span className="text-slate-600">Trend Historisch</span>
                    </div>
                    {forecastTrendData.length > 0 && (
                        <>
                            <div className="flex items-center gap-2">
                                <div className="h-1 w-6 rounded-full bg-orange-500" style={{ 
                                    background: "repeating-linear-gradient(90deg, #f97316 0px, #f97316 8px, transparent 8px, transparent 12px)" 
                                }}></div>
                                <span className="text-slate-600">Trend Prognose</span>
                            </div>
                            {lastHistoricalDate && (
                                <div className="flex items-center gap-2">
                                    <div className="h-4 w-px bg-slate-400" style={{ borderLeft: "2px dashed #94a3b8" }}></div>
                                    <span className="text-slate-600">Trennlinie</span>
                                </div>
                            )}
                        </>
                    )}
                </>
            )}
            {metric === "Ø Score" && forecastData.length > 0 && (
                <>
                    <div className="flex items-center gap-2">
                        <div className="h-1 w-6 rounded-full bg-orange-500" style={{
                            background: "repeating-linear-gradient(90deg, #f97316 0px, #f97316 8px, transparent 8px, transparent 12px)"
                        }}></div>
                        <span className="text-slate-600">Prognose</span>
                    </div>
                    {lastHistoricalDate && (
                        <div className="flex items-center gap-2">
                            <div className="h-4 w-px bg-slate-400" style={{ borderLeft: "2px dashed #94a3b8" }}></div>
                            <span className="text-slate-600">Trennlinie</span>
                        </div>
                    )}
                </>
            )}
            {metric === "Ø Score" && anomalyMarks.length > 0 && (
                <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 border-2 border-white shadow-sm"></span>
                    <span className="text-slate-600">Anomalie ▼</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white shadow-sm ml-1"></span>
                    <span className="text-slate-600">Anomalie ▲</span>
                </div>
            )}
        </div>
    )

    // Summary stats component (reusable) — clean inline numbers
    const Stat = ({ label, value, tone = "default" }) => {
        const toneClass = tone === "good" ? "text-emerald-700"
                        : tone === "bad"  ? "text-rose-700"
                        : tone === "info" ? "text-blue-700"
                        : tone === "warn" ? "text-amber-700"
                        : "text-slate-900";
        return (
            <div className="flex flex-col items-center text-center px-2">
                <span className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">{label}</span>
                <span className={`font-semibold tnum text-[16px] tracking-tight ${toneClass}`}>{value}</span>
            </div>
        )
    }

    const SummaryStats = () => {
        if (timelineData.length === 0) return null

        if (metric === "Anzahl") {
            const total   = timelineData.reduce((s, d) => s + (d.count || 0), 0)
            const avg     = (total / timelineData.length).toFixed(1)
            const maxCnt  = Math.max(...timelineData.map(d => d.count || 0))
            return (
                <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-3 divide-x divide-slate-100">
                    <Stat label="Datenpunkte" value={timelineData.length} />
                    <Stat label="Ø Anzahl"    value={avg}    tone="info" />
                    <Stat label="Max Anzahl"  value={maxCnt} tone="info" />
                </div>
            )
        }

        if (metric === "Trend") {
            const avgTrend = trendData.length > 1
                ? trendData.slice(1).reduce((s, d) => s + d.trend, 0) / (trendData.length - 1)
                : 0
            const maxTrend = trendData.length ? Math.max(...trendData.map(d => d.trend)) : 0
            const minTrend = trendData.length ? Math.min(...trendData.map(d => d.trend)) : 0
            const fmt = (v) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}`
            return (
                <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-3 divide-x divide-slate-100">
                    <Stat label="Datenpunkte" value={timelineData.length} />
                    <Stat label="Ø Trend"     value={fmt(avgTrend)} tone={avgTrend >= 0 ? "good" : "bad"} />
                    <Stat label="Max / Min"   value={`${fmt(maxTrend)} / ${minTrend.toFixed(2)}`} />
                </div>
            )
        }

        const avgHist = (timelineData.reduce((s, d) => s + d.score, 0) / timelineData.length).toFixed(2)
        const avgFore = forecastData.length
            ? (forecastData.reduce((s, d) => s + d.score, 0) / forecastData.length).toFixed(2)
            : null
        return (
            <div className={`mt-3 pt-3 border-t border-slate-100 grid ${avgFore ? "grid-cols-3" : "grid-cols-2"} divide-x divide-slate-100`}>
                <Stat label="Datenpunkte"  value={timelineData.length} />
                <Stat label="Ø Historisch" value={avgHist} tone="info" />
                {avgFore && <Stat label="Ø Prognose" value={avgFore} tone="warn" />}
            </div>
        )
    }

    // Single state-message for empty/error — rendered INSIDE the chart area so
    // the surrounding card + Dialog never unmount when the user changes filters.
    const emptyMessage =
        !companyId ? "Keine Firma ausgewählt"
        : error    ? `Fehler: ${error}`
        : chartData.length === 0 ? "Keine Daten für diesen Zeitraum verfügbar"
        : null

    const showOverlay = loading || refreshing
    const overlayLabel = loading ? "Lade Timeline-Daten…" : "Daten werden aktualisiert…"

    return (
        <>
            {/* Main Card — flex-col + h-full damit Inhalt Card-Höhe nutzt */}
            <div
                className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer flex flex-col h-full"
                onClick={() => setModalOpen(true)}
            >
                <ChartCardHeader
                    icon={<TrendUpIcon />}
                    eyebrow="ZEITREIHE · HISTORIE & PROGNOSE"
                    title="Timeline"
                    subtitle={`${SOURCE_LABEL[source]} · ${metric}`}
                    expandable
                    actions={<FilterDropdowns compact />}
                />

                {/* Content nimmt restliche Card-Höhe ein, Stats werden via flex-1 Spacer an Boden gedrückt */}
                <div className="px-4 pt-4 pb-4 flex flex-col flex-1 min-h-0">
                    <div className="w-full flex-shrink-0">
                        <div id="timeline-chart-export" className="relative h-[220px] w-full">
                            {emptyMessage && !showOverlay ? (
                                <div className="h-full flex items-center justify-center">
                                    <p className="text-[13px] text-slate-500">{emptyMessage}</p>
                                </div>
                            ) : (
                                <TimelineChart height={220} />
                            )}
                            {showOverlay && (
                                <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
                                    <div className="flex items-center gap-2">
                                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                                        <p className="text-slate-600 text-[12px]">{overlayLabel}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                        <ChartLegend />
                    </div>
                    {timelineHasGaps && (
                        <p className="text-[11px] text-slate-500 text-center italic flex items-center justify-center gap-1.5 mt-2">
                            <span className="inline-block w-5 h-0 border-t border-dashed border-slate-400"></span>
                            Gestrichelte Linie = interpolierte Werte
                        </p>
                    )}

                    {/* Spacer drückt Stats + Footer an Karten-Boden */}
                    <div className="flex-1" />

                    <SummaryStats />

                    <p className="text-[11px] text-slate-400 text-center mt-3">
                        Karte anklicken zum Vergrössern
                    </p>
                </div>
            </div>

            {/* Modal */}
            <Dialog open={modalOpen} onOpenChange={setModalOpen}>
                <DialogContent
                    className="overflow-hidden flex flex-col p-0 gap-0"
                    style={{
                        width: '90vw',
                        maxWidth: '90vw',
                        height: '85vh',
                        maxHeight: '85vh'
                    }}
                >
                    <span aria-hidden="true" className="block h-[3px] w-full bg-blue-500" />
                    <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start justify-between gap-3 flex-shrink-0">
                        <div className="flex items-start gap-2.5">
                            <span className="w-9 h-9 rounded-md grid place-items-center bg-blue-50 text-blue-600 flex-none">
                                <TrendUpIcon className="w-[18px] h-[18px]" />
                            </span>
                            <div>
                                <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                                    ZEITREIHE · HISTORIE & PROGNOSE
                                </p>
                                <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900">
                                    Timeline
                                </DialogTitle>
                                <p className="m-0 mt-0.5 text-[11px] text-slate-500">
                                    {SOURCE_LABEL[source]} · {metric}
                                </p>
                            </div>
                        </div>
                        <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 flex-wrap justify-end">
                            <FilterDropdowns />
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col min-h-0 px-5 py-4">
                        {/* Large Chart */}
                        <div className="flex-1 min-h-0 relative overflow-hidden">
                            {emptyMessage && !showOverlay ? (
                                <div className="h-full flex items-center justify-center">
                                    <p className="text-[13px] text-slate-500">{emptyMessage}</p>
                                </div>
                            ) : (
                                <TimelineChart height="100%" />
                            )}
                            {showOverlay && (
                                <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
                                    <div className="flex items-center gap-2">
                                        <div className="animate-spin rounded-full h-6 w-6 border-2 border-slate-200 border-t-slate-600"></div>
                                        <p className="text-slate-700 text-[12px] font-medium">{overlayLabel}</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        <ChartLegend compact={true} />
                        {timelineHasGaps && (
                            <p className="text-xs text-slate-500 text-center italic flex items-center justify-center gap-1 mt-2 flex-shrink-0">
                                <span className="inline-block w-6 h-0 border-t-2 border-dashed border-slate-400"></span>
                                Gestrichelte Linie = Keine Daten vorhanden (interpoliert)
                            </p>
                        )}

                        {/* Extended Stats in Modal - Compact */}
                        {timelineData.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-3 flex-shrink-0">
                                {metric === "Anzahl" ? (
                                    <>
                                        <div className="text-center p-2 bg-slate-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Datenpunkte</p>
                                            <p className="text-lg font-bold text-slate-800">{timelineData.length}</p>
                                        </div>
                                        <div className="text-center p-2 bg-blue-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Ø Anzahl</p>
                                            <p className="text-lg font-bold text-blue-600">
                                                {(timelineData.reduce((sum, d) => sum + (d.count || 0), 0) / timelineData.length).toFixed(1)}
                                            </p>
                                        </div>
                                        <div className="text-center p-2 bg-blue-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Max Anzahl</p>
                                            <p className="text-lg font-bold text-blue-600">
                                                {Math.max(...timelineData.map(d => d.count || 0))}
                                            </p>
                                        </div>
                                        <div className="text-center p-2 bg-slate-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Gesamt</p>
                                            <p className="text-lg font-bold text-slate-800">
                                                {timelineData.reduce((sum, d) => sum + (d.count || 0), 0)}
                                            </p>
                                        </div>
                                    </>
                                ) : metric === "Trend" ? (
                                    <>
                                        <div className="text-center p-2 bg-slate-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Datenpunkte</p>
                                            <p className="text-lg font-bold text-slate-800">{timelineData.length}</p>
                                        </div>
                                        <div className="text-center p-2 bg-green-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Ø Trend</p>
                                            <p className={`text-lg font-bold ${
                                                trendData.length > 1 && (trendData.slice(1).reduce((sum, d) => sum + d.trend, 0) / (trendData.length - 1)) >= 0
                                                    ? 'text-green-600' 
                                                    : 'text-red-600'
                                            }`}>
                                                {trendData.length > 1 
                                                    ? ((trendData.slice(1).reduce((sum, d) => sum + d.trend, 0) / (trendData.length - 1)) >= 0 ? '+' : '') + 
                                                      (trendData.slice(1).reduce((sum, d) => sum + d.trend, 0) / (trendData.length - 1)).toFixed(2)
                                                    : '0.00'}
                                            </p>
                                        </div>
                                        <div className="text-center p-2 bg-green-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Max Trend</p>
                                            <p className="text-lg font-bold text-green-600">
                                                {trendData.length > 0 ? Math.max(...trendData.map(d => d.trend)).toFixed(2) : "0.00"}
                                            </p>
                                        </div>
                                        <div className="text-center p-2 bg-red-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Min Trend</p>
                                            <p className="text-lg font-bold text-red-600">
                                                {trendData.length > 0 ? Math.min(...trendData.map(d => d.trend)).toFixed(2) : "0.00"}
                                            </p>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="text-center p-2 bg-slate-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Datenpunkte</p>
                                            <p className="text-lg font-bold text-slate-800">{timelineData.length}</p>
                                        </div>
                                        <div className="text-center p-2 bg-blue-50 rounded-lg">
                                            <p className="text-xs text-slate-500 mb-0.5">Ø Historisch</p>
                                            <p className="text-lg font-bold text-blue-600">
                                                {(timelineData.reduce((sum, d) => sum + d.score, 0) / timelineData.length).toFixed(2)}
                                            </p>
                                        </div>
                                        {forecastData.length > 0 && (
                                            <>
                                                <div className="text-center p-2 bg-orange-50 rounded-lg">
                                                    <p className="text-xs text-slate-500 mb-0.5">Ø Prognose</p>
                                                    <p className="text-lg font-bold text-orange-500">
                                                        {(forecastData.reduce((sum, d) => sum + d.score, 0) / forecastData.length).toFixed(2)}
                                                    </p>
                                                </div>
                                                <div className="text-center p-2 bg-slate-50 rounded-lg">
                                                    <p className="text-xs text-slate-500 mb-0.5">Trend</p>
                                                    <p className={`text-lg font-bold ${
                                                        forecastData[forecastData.length - 1]?.score > timelineData[timelineData.length - 1]?.score 
                                                            ? 'text-green-600' 
                                                            : 'text-red-600'
                                                    }`}>
                                                        {forecastData[forecastData.length - 1]?.score > timelineData[timelineData.length - 1]?.score 
                                                            ? '↑ Steigend' 
                                                            : '↓ Fallend'}
                                                    </p>
                                                </div>
                                            </>
                                        )}
                                    </>
                                )}
                            </div>
                        )}

                        <div className="mt-3 flex items-center justify-end flex-shrink-0">
                            <p className="text-xs text-slate-400">
                                {SOURCE_LABEL[source]} · {metric} · Historie + Prognose
                            </p>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    )
})
