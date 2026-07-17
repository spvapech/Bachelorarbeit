import * as React from "react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import { Filter, ChevronDown, Maximize2, Calendar, Hash, Eye, Check } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useEffect, useMemo, useState, memo } from "react"
import { API_URL } from "@/config"
import { ChartCardHeader, SourceToggle, DropdownPicker } from "./ChartHeader"
import { Star } from "../../icons"

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

function parseYearMonth(period) {
  if (!period) return null
  const [y, m] = String(period).split("-").map(Number)
  if (!y || !m) return null
  return { year: y, month: m }
}

function periodToIndex(period, granularity) {
  if (!period) return null
  if (granularity === "year") {
    const parsed = parseYearMonth(period)
    if (!parsed) return null
    return parsed.year * 12 + (parsed.month - 1)
  }
  const year = parseYear(period)
  return year != null ? year : null
}

function formatGapRange(fromPeriod, toPeriod, granularity) {
  if (!fromPeriod || !toPeriod) return ""
  if (granularity === "year") {
    const fromLabel = formatMonthLabel(fromPeriod)
    const toLabel = formatMonthLabel(toPeriod)
    return `${fromLabel} - ${toLabel}`
  }
  return `${fromPeriod} - ${toPeriod}`
}

function formatMonthLabel(period) {
  if (!period) return ""
  const [y, m] = String(period).split("-").map(Number)
  if (!y || !m) return period
  const date = new Date(Date.UTC(y, m - 1, 1))
  return date.toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

function prettifyTopicKey(key) {
  if (!key) return ""
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

// Memoized TopicRatingCard für bessere Performance
export const TopicRatingCard = memo(function TopicRatingCard({ companyId, onFiltersChange, onLoadingChange, globalTimeRange = "all" }) {
  // Defaults
  const [source, setSource] = useState("employee")
  const [granularity, setGranularity] = useState("overall")

  const [topics, setTopics] = useState([])
  const [rawData, setRawData] = useState([])

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)

  const [modalOpen, setModalOpen] = useState(false)

  // Jahr-View (Monatsdaten) braucht selectedYear
  const [selectedYear, setSelectedYear] = useState(null)
  // Jahre aus DB (separat laden, nicht aus rawData ableiten!)
  const [years, setYears] = useState([])


  // Topics ein/ausblenden
  const [hiddenTopics, setHiddenTopics] = useState(() => new Set())
  
  // Kommuniziere Loading-State nach außen
  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(loading);
    }
  }, [loading, onLoadingChange]);

  // Farbpalette
  const palette = [
    "#3b82f6",
    "#f97316",
    "#10b981",
    "#a855f7",
    "#ef4444",
    "#14b8a6",
    "#eab308",
    "#6366f1",
    "#f43f5e",
    "#0ea5e9",
    "#84cc16",
    "#d946ef",
  ]
  const topicColor = (idx) => palette[idx % palette.length]

  useEffect(() => {
    if (!companyId) return

    const fetchYears = async () => {
      try {
        // Jahre immer aus der DB über API holen:
        const url =
          `${API_URL}/analytics/company/${companyId}/topic-ratings-timeseries` +
          `?source=${source}&granularity=year`

        const res = await fetch(url)
        if (!res.ok) throw new Error(`API Error (years): ${res.status}`)
        const json = await res.json()

        const ys = (json.data || [])
          .map((d) => parseYear(d.period))
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
        // selectedYear nicht hart nullen, nur wenn du willst
      }
    }

    fetchYears()
  }, [companyId, source, granularity])


  // Fetch
  useEffect(() => {
    if (!companyId) return

    const fetchData = async () => {
      const isFirst = rawData.length === 0
      isFirst ? setLoading(true) : setRefreshing(true)

      try {
        setError(null)

        // UI granularity -> API granularity mapping
        const apiGranularity = granularity === "overall" ? "year" : "month"

        let url =
          `${API_URL}/analytics/company/${companyId}/topic-ratings-timeseries` +
          `?source=${source}&granularity=${apiGranularity}`

        // Wenn "Jahr"-Modus: Monate innerhalb selectedYear anzeigen
        if (granularity === "year") {
          if (selectedYear) {
            const start = `${selectedYear}-01-01`
            const end = `${selectedYear}-12-31`
            url += `&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
          } else {
            // Falls selectedYear noch nicht da ist: warte auf years-effect
            // (nicht topics/rawData wipen — sonst unmountet das Dialog kurz)
            setLoading(false)
            setRefreshing(false)
            return
          }
        } else if (globalTimeRange !== "all") {
          // Globaler Zeitfilter im "overall"-Modus
          const now = new Date()
          const years = globalTimeRange === "1y" ? 1 : 3
          const startDate = new Date(now.getFullYear() - years, now.getMonth(), now.getDate())
          url += `&start=${encodeURIComponent(startDate.toISOString().slice(0, 10))}`
        }


        const res = await fetch(url)
        if (!res.ok) throw new Error(`API Error: ${res.status}`)
        const json = await res.json()

        setTopics(json.topics || [])
        setRawData(json.data || [])



        // Reset: standardmäßig nur Top 5 sichtbar
        const allTopics = json.topics || []
        const top5 = [...allTopics]
          .sort((a, b) => {
            const countA = (json.data || []).filter(row => row?.[a] != null).length
            const countB = (json.data || []).filter(row => row?.[b] != null).length
            return countB - countA
          })
          .slice(0, 5)
        const toHide = allTopics.filter(t => !top5.includes(t))
        setHiddenTopics(new Set(toHide))
      } catch (e) {
        console.error("Error fetching topic ratings:", e)
        setError(e.message)
        setTopics([])
        setRawData([])
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    }

    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyId, source, granularity, selectedYear, globalTimeRange])

  // Top-5 Topics nach Häufigkeit (wie oft Werte vorhanden)
  const topicCounts = useMemo(() => {
    const counts = {}
    for (const t of topics || []) counts[t] = 0

    for (const row of rawData || []) {
      for (const t of topics || []) {
        if (row?.[t] !== null && row?.[t] !== undefined) counts[t] += 1
      }
    }
    return counts
  }, [topics, rawData])

  const top5Topics = useMemo(() => {
    return [...(topics || [])]
      .sort((a, b) => (topicCounts[b] || 0) - (topicCounts[a] || 0))
      .slice(0, 5)
  }, [topics, topicCounts])

  // baseTopics ist immer Top 5 für die Standard-Anzeige
  const baseTopics = useMemo(() => {
    return top5Topics
  }, [top5Topics])

  // visibleTopics: alle nicht-hidden Topics (kann mehr als Top 5 sein, wenn User manuell auswählt)
  const visibleTopics = useMemo(() => {
    return (topics || []).filter((t) => !hiddenTopics.has(t))
  }, [topics, hiddenTopics])

  // Chart Daten: nur periodLabel setzen (kein Slider)
  const chartData = useMemo(() => {
    const rows = Array.isArray(rawData) ? [...rawData] : []
    const sorted = rows
      .map((row) => ({ row, idx: periodToIndex(row?.period, granularity) }))
      .filter((item) => item.idx != null)
      .sort((a, b) => a.idx - b.idx)
      .map((item) => item.row)

    const gapRow = (fromPeriod, toPeriod) => {
      const empty = {
        period: `gap-${fromPeriod}-${toPeriod}`,
        periodLabel: "gab",
        _isGap: true,
        _gapInfo: formatGapRange(fromPeriod, toPeriod, granularity),
        _gapMarker: 0,
      }
      for (const t of topics || []) {
        empty[t] = null
      }
      return empty
    }

    const withGaps = []
    for (let i = 0; i < sorted.length; i += 1) {
      const current = sorted[i]
      if (i > 0) {
        const prev = sorted[i - 1]
        const prevIdx = periodToIndex(prev?.period, granularity)
        const curIdx = periodToIndex(current?.period, granularity)
        if (prevIdx != null && curIdx != null && curIdx - prevIdx > 1) {
          withGaps.push(gapRow(prev?.period, current?.period))
        }
      }
      withGaps.push(current)
    }

    // Add gap bridge data for dashed line visualization
    const withGapBridges = withGaps.map((row, idx) => {
      const newRow = { ...row }
      if (!row._isGap) {
        // Check if this is adjacent to a gap
        const isBeforeGap = idx + 1 < withGaps.length && withGaps[idx + 1]._isGap
        const isAfterGap = idx - 1 >= 0 && withGaps[idx - 1]._isGap
        if (isBeforeGap || isAfterGap) {
          for (const t of topics || []) {
            if (newRow[t] != null) {
              newRow[`${t}__gap`] = newRow[t]
            }
          }
        }
      } else {
        // Gap row - interpolate values for dashed line
        const prevIdx = idx - 1
        const nextIdx = idx + 1
        if (prevIdx >= 0 && nextIdx < withGaps.length) {
          for (const t of topics || []) {
            const prevVal = withGaps[prevIdx][t]
            const nextVal = withGaps[nextIdx][t]
            if (prevVal != null && nextVal != null) {
              newRow[`${t}__gap`] = +((prevVal + nextVal) / 2).toFixed(2)
            }
          }
        }
      }
      return newRow
    })

    return withGapBridges.map((row) => ({
      ...row,
      periodLabel: row.periodLabel || (granularity === "year" ? formatMonthLabel(row.period) : row.period),
    }))
  }, [rawData, granularity, topics])

  const gapNotes = useMemo(() => {
    const notes = (chartData || [])
      .filter((row) => row?._isGap && row?._gapInfo)
      .map((row) => row._gapInfo)
    return Array.from(new Set(notes))
  }, [chartData])

  // ── Summary-Stats unter dem Chart (Topic-weite Aggregation) ──────────────
  // Berechnet: Datenpunkte, Ø über alle sichtbaren Topics,
  // bestes / schlechtestes Topic basierend auf dem Durchschnitt.
  const topicStats = useMemo(() => {
    if (!chartData?.length || !visibleTopics?.length) return null

    const nonGap = chartData.filter((r) => !r?._isGap)
    if (!nonGap.length) return null

    const perTopicAvg = {}
    for (const t of visibleTopics) {
      const vals = nonGap
        .map((r) => Number(r?.[t]))
        .filter((v) => Number.isFinite(v))
      if (vals.length) {
        perTopicAvg[t] = vals.reduce((s, v) => s + v, 0) / vals.length
      }
    }

    const entries = Object.entries(perTopicAvg)
    if (!entries.length) return null

    const overall = entries.reduce((s, [, v]) => s + v, 0) / entries.length
    const best  = entries.reduce((b, c) => (c[1] > b[1] ? c : b), entries[0])
    const worst = entries.reduce((w, c) => (c[1] < w[1] ? c : w), entries[0])

    return {
      dataPoints: nonGap.length,
      avgOverall: overall,
      visibleCount: visibleTopics.length,
      bestTopic:  { name: prettifyTopicKey(best[0]),  score: best[1]  },
      worstTopic: { name: prettifyTopicKey(worst[0]), score: worst[1] },
    }
  }, [chartData, visibleTopics])

  // Tonale Klassen wie im Dashboard (good ≥ 3.5, warn 2.5-3.5, bad < 2.5)
  const scoreColorClass = (s) =>
    !Number.isFinite(s) ? "text-slate-700"
      : s >= 3.5 ? "text-emerald-700"
      : s >= 2.5 ? "text-amber-700"
      : "text-rose-700"

  // Export Filter-State nach außen (für PDF Export)
  useEffect(() => {
    if (onFiltersChange && !loading) {
      const stats = {
        dataPoints: chartData.length,
        topicsCount: visibleTopics.length,
        topTopics: visibleTopics.slice(0, 3).map(t => prettifyTopicKey(t)),
        avgScore: topicStats?.avgOverall ? topicStats.avgOverall.toFixed(2) : null,
        bestTopic: topicStats?.bestTopic ? { name: topicStats.bestTopic.name, score: topicStats.bestTopic.score.toFixed(2) } : null,
        worstTopic: topicStats?.worstTopic ? { name: topicStats.worstTopic.name, score: topicStats.worstTopic.score.toFixed(2) } : null,
      };

      onFiltersChange({
        source,
        granularity,
        selectedYear,
        visibleTopics,
        allTopics: topics || [],
        stats
      });
    }
  }, [source, granularity, selectedYear, visibleTopics, chartData, loading, topicStats, onFiltersChange, topics]);

  // Tooltip
  // Tooltip — slate-900 dark style mit Mono-Zahlen
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null

    const gapInfo = payload?.[0]?.payload?._isGap ? payload?.[0]?.payload?._gapInfo : null

    if (gapInfo) {
      return (
        <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] max-w-[260px]">
          <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1">Lücke</p>
          <p className="text-amber-400 inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Keine Bewertungen
          </p>
          <p className="text-slate-500 mt-0.5 text-[11px]">{gapInfo}</p>
        </div>
      )
    }

    const items = payload
      .filter((p) => p.dataKey !== "_gapMarker" && !p.dataKey.endsWith("__gap") && p.value != null)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))

    return (
      <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] max-w-[300px]">
        <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{label}</p>
        <div className="space-y-0.5">
          {items.map((p) => (
            <div key={p.dataKey} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-1.5 min-w-0">
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: p.stroke }}
                />
                <span className="text-slate-300 truncate">
                  {prettifyTopicKey(p.dataKey)}
                </span>
              </div>
              <span className="font-semibold tnum text-white">
                {Number(p.value).toFixed(2).replace(".", ",")}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Filter UI
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
        label="Zeit"
        value={GRANULARITY_LABEL[granularity]}
        icon={<Calendar />}
        compact={compact}
        options={[
          { value: "overall", label: "ges. Zeitraum" },
          { value: "year",    label: "Jahr" },
        ]}
        onChange={(v) => {
          setGranularity(v)
          if (v === "overall") setSelectedYear(null)
        }}
      />

      {granularity === "year" && (
        <DropdownPicker
          label="Jahr"
          value={selectedYear ? String(selectedYear) : "—"}
          compact={compact}
          options={years.map((y) => ({ value: y, label: String(y) }))}
          onChange={setSelectedYear}
        />
      )}

      {/* Topic multi-select dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            title={`Topics ${visibleTopics.length}/${(topics || []).length}`}
            className={[
              "h-7 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium",
              "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50",
              compact ? "px-2" : "px-2.5",
              "[&_svg]:flex-none [&_svg]:w-3.5 [&_svg]:h-3.5",
            ].join(" ")}
          >
            <Eye className="text-slate-500" />
            {!compact && <span className="text-slate-500">Topics:</span>}
            <span className="text-slate-900 tnum">{visibleTopics.length}/{(topics || []).length}</span>
            <ChevronDown className="text-slate-400" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-72 max-h-[420px] overflow-y-auto p-0">
          <div className="px-3 py-2 border-b border-slate-200 bg-slate-50 flex items-center justify-between sticky top-0">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500">Topics</span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                if (hiddenTopics.size === 0) setHiddenTopics(new Set(topics || []))
                else setHiddenTopics(new Set())
              }}
              className="text-[11px] text-blue-700 hover:text-blue-800 font-medium"
            >
              {hiddenTopics.size === 0 ? "Alle abwählen" : "Alle auswählen"}
            </button>
          </div>
          <div className="py-1">
            {(topics || []).map((t, idx) => {
              const hidden = hiddenTopics.has(t)
              return (
                <button
                  key={t}
                  onClick={(e) => {
                    e.stopPropagation()
                    setHiddenTopics((prev) => {
                      const next = new Set(prev)
                      if (next.has(t)) next.delete(t)
                      else next.add(t)
                      return next
                    })
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-slate-50 transition-colors text-left"
                >
                  <span
                    className={[
                      "w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors",
                      hidden ? "bg-white border-slate-300" : "bg-slate-900 border-slate-900",
                    ].join(" ")}
                  >
                    {!hidden && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                  </span>
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: topicColor(idx) }}
                  />
                  <span className={["text-[12px] flex-1 truncate", hidden ? "text-slate-400" : "text-slate-800"].join(" ")}>
                    {prettifyTopicKey(t)}
                  </span>
                </button>
              )
            })}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  )

  const TopicChart = ({ height = 200 }) => (
    <ResponsiveContainer width="100%" height={height === "100%" ? "100%" : height}>
      <LineChart data={chartData} margin={{ left: 0, right: 16, top: 8, bottom: 5 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="periodLabel"
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
          tickFormatter={(v) => Number(v).toFixed(1)}
        />
        <Tooltip
          content={<CustomTooltip />}
          cursor={{ stroke: "#cbd5e1", strokeWidth: 1, strokeDasharray: "3 3" }}
        />

        {visibleTopics.map((topic) => {
          const colorIdx = (topics || []).indexOf(topic)
          const color = topicColor(Math.max(colorIdx, 0))
          return (
            <Line
              key={topic}
              type="monotone"
              dataKey={topic}
              stroke={color}
              strokeWidth={1.75}
              dot={false}
              activeDot={{ r: 4, fill: color, stroke: "#fff", strokeWidth: 2 }}
              connectNulls={false}
              name={prettifyTopicKey(topic)}
            />
          )
        })}

        {/* Dashed gap bridge lines for each visible topic — deutlich sichtbar */}
        {visibleTopics.map((topic) => {
          const colorIdx = (topics || []).indexOf(topic)
          return (
            <Line
              key={`${topic}__gap`}
              type="monotone"
              dataKey={`${topic}__gap`}
              stroke={topicColor(Math.max(colorIdx, 0))}
              strokeWidth={1.75}
              strokeDasharray="5 3"
              strokeOpacity={0.7}
              dot={false}
              activeDot={false}
              connectNulls={false}
              legendType="none"
              isAnimationActive={false}
            />
          )
        })}

        <Line
          type="monotone"
          dataKey="_gapMarker"
          stroke="transparent"
          strokeWidth={0}
          dot={false}
          activeDot={false}
          connectNulls={false}
          legendType="none"
          isAnimationActive={false}
        />

      </LineChart>
    </ResponsiveContainer>
  )



  // Single empty/error message used in both card + modal chart areas
  const emptyMessage =
    !companyId ? "Keine Firma ausgewählt"
    : error    ? `Fehler: ${error}`
    : (!chartData.length || !topics.length) ? "Keine Daten verfügbar"
    : null

  const showOverlay = loading || refreshing
  const overlayLabel = loading ? "Daten werden geladen…" : "Daten werden aktualisiert…"

  return (
    <>
      {/* Card — flex-col + h-full damit Stats am Boden sitzen */}
      <div
        className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer flex flex-col h-full"
        onClick={() => setModalOpen(true)}
      >
        <ChartCardHeader
          icon={<Star />}
          eyebrow="TOPIC-BEWERTUNGEN"
          title="Topics im Detail"
          subtitle={`${SOURCE_LABEL[source]} · ${visibleTopics.length}/${(topics || []).length} Topics${granularity === "year" && selectedYear ? ` · ${selectedYear}` : " · ges. Zeitraum"}`}
          expandable
          actions={<FilterDropdowns compact />}
        />

        <div className="px-4 pt-4 pb-4 flex flex-col flex-1 min-h-0">
          <div className="w-full border-0 outline-none flex-shrink-0">
            <div id="topic-rating-chart-export" className="relative h-[220px] w-full">
              {emptyMessage && !showOverlay ? (
                <div className="h-full flex items-center justify-center">
                  <p className="text-[13px] text-slate-500">{emptyMessage}</p>
                </div>
              ) : (
                <TopicChart height={220} />
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

            {visibleTopics.length > 0 && !emptyMessage && (
              <div className="mt-4 flex items-center justify-center gap-x-4 gap-y-1 flex-wrap text-[11px]">
                {visibleTopics.slice(0, 6).map((topic) => {
                  const colorIdx = (topics || []).indexOf(topic)
                  return (
                    <span key={topic} className="inline-flex items-center gap-1.5">
                      <span
                        className="inline-block w-3 h-1 rounded-full flex-none"
                        style={{ background: topicColor(Math.max(colorIdx, 0)) }}
                      />
                      <span className="text-slate-600 truncate max-w-[120px]">
                        {prettifyTopicKey(topic)}
                      </span>
                    </span>
                  )
                })}
                {visibleTopics.length > 6 && (
                  <span className="text-slate-400">+ {visibleTopics.length - 6}</span>
                )}
              </div>
            )}
          </div>

          {gapNotes.length > 0 && (
            <p className="text-[11px] text-slate-500 text-center mt-2 italic flex items-center justify-center gap-1.5">
              <span className="inline-block w-5 h-0 border-t border-dashed border-slate-400"></span>
              Gestrichelte Linie = keine Bewertungen ({gapNotes.join(", ")})
            </p>
          )}

          {/* Spacer drückt Stats + Footer an den Karten-Boden */}
          <div className="flex-1" />

          {/* Summary-Stats unter dem Chart — identische Struktur wie Timeline-Card */}
          {topicStats && (() => {
            const avgTone = topicStats.avgOverall >= 3.5 ? "text-emerald-700"
                          : topicStats.avgOverall >= 2.5 ? "text-amber-700"
                          : "text-rose-700";
            return (
              <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-3 divide-x divide-slate-100">
                <div className="flex flex-col items-center text-center px-2">
                  <span className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Datenpunkte</span>
                  <span className="font-semibold tnum text-[16px] tracking-tight text-slate-900">
                    {topicStats.dataPoints}
                  </span>
                </div>
                <div className="flex flex-col items-center text-center px-2">
                  <span className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Ø Score</span>
                  <span className={`font-semibold tnum text-[16px] tracking-tight ${avgTone}`}>
                    {topicStats.avgOverall.toFixed(2).replace(".", ",")}
                  </span>
                </div>
                <div className="flex flex-col items-center text-center px-2">
                  <span className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Topics</span>
                  <span className="font-semibold tnum text-[16px] tracking-tight text-slate-900">
                    {topicStats.visibleCount}
                  </span>
                </div>
              </div>
            );
          })()}

          <p className="text-[11px] text-slate-400 text-center mt-3">Karte anklicken zum Vergrössern</p>
        </div>
      </div>

      {/* Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent
          className="overflow-hidden flex flex-col p-0 gap-0"
          style={{ width: "90vw", maxWidth: "90vw", height: "85vh", maxHeight: "85vh" }}
        >
          <span aria-hidden="true" className="block h-[3px] w-full bg-amber-500" />
          <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start justify-between gap-3 flex-shrink-0">
            <div className="flex items-start gap-2.5">
              <span className="w-9 h-9 rounded-md grid place-items-center bg-amber-50 text-amber-600 flex-none">
                <Star className="w-[18px] h-[18px]" />
              </span>
              <div>
                <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                  TOPIC-BEWERTUNGEN · DETAILANSICHT
                </p>
                <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900">
                  Topics im Detail
                </DialogTitle>
                <p className="m-0 mt-0.5 text-[11px] text-slate-500">
                  {SOURCE_LABEL[source]} · {visibleTopics.length}/{(topics || []).length} Topics{granularity === "year" && selectedYear ? ` · ${selectedYear}` : " · ges. Zeitraum"}
                </p>
              </div>
            </div>
            <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 flex-wrap justify-end">
              <FilterDropdowns />
            </div>
          </div>

          <div className="flex-1 flex flex-col min-h-0 px-5 py-4">
            <div className="relative flex-1 min-h-0">
              {emptyMessage && !showOverlay ? (
                <div className="h-full flex items-center justify-center">
                  <p className="text-[13px] text-slate-500">{emptyMessage}</p>
                </div>
              ) : (
                <TopicChart height="100%" />
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

            {/* Externe Legende im Modal */}
            {visibleTopics.length > 0 && !emptyMessage && (
              <div className="mt-3 flex items-center justify-center gap-x-4 gap-y-1 flex-wrap text-[12px] flex-shrink-0">
                {visibleTopics.map((topic) => {
                  const colorIdx = (topics || []).indexOf(topic)
                  return (
                    <span key={topic} className="inline-flex items-center gap-1.5">
                      <span
                        className="inline-block w-3.5 h-1 rounded-full flex-none"
                        style={{ background: topicColor(Math.max(colorIdx, 0)) }}
                      />
                      <span className="text-slate-600">{prettifyTopicKey(topic)}</span>
                    </span>
                  )
                })}
              </div>
            )}

            {/* Erweiterte Summary-Stats unter dem Chart */}
            {topicStats && (
              <div className="mt-4 pt-3 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-3 flex-shrink-0">
                <div className="text-center px-3 py-2 bg-slate-50 rounded-md border border-slate-200">
                  <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Datenpunkte</p>
                  <p className="text-[18px] font-semibold tnum text-slate-900">{topicStats.dataPoints}</p>
                </div>
                <div className={`text-center px-3 py-2 rounded-md border ${
                  topicStats.avgOverall >= 3.5 ? "bg-emerald-50 border-emerald-200"
                  : topicStats.avgOverall >= 2.5 ? "bg-amber-50 border-amber-200"
                  : "bg-rose-50 border-rose-200"
                }`}>
                  <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Ø Score</p>
                  <p className={`text-[18px] font-semibold tnum ${scoreColorClass(topicStats.avgOverall)}`}>
                    {topicStats.avgOverall.toFixed(2).replace(".", ",")}
                  </p>
                </div>
                <div className="text-center px-3 py-2 bg-emerald-50 rounded-md border border-emerald-200">
                  <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Bestes Topic</p>
                  <p className="text-[12px] font-semibold text-emerald-700 truncate" title={topicStats.bestTopic.name}>
                    {topicStats.bestTopic.name}
                  </p>
                  <p className="text-[11px] tnum text-emerald-700 mt-0.5">
                    Ø {topicStats.bestTopic.score.toFixed(2).replace(".", ",")}
                  </p>
                </div>
                <div className="text-center px-3 py-2 bg-rose-50 rounded-md border border-rose-200">
                  <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Schlechtestes Topic</p>
                  <p className="text-[12px] font-semibold text-rose-700 truncate" title={topicStats.worstTopic.name}>
                    {topicStats.worstTopic.name}
                  </p>
                  <p className="text-[11px] tnum text-rose-700 mt-0.5">
                    Ø {topicStats.worstTopic.score.toFixed(2).replace(".", ",")}
                  </p>
                </div>
              </div>
            )}

            <div className="mt-3 flex items-center justify-between flex-shrink-0 gap-3 flex-wrap">
              <button
                onClick={() => {
                  const toHide = (topics || []).filter((t) => !top5Topics.includes(t))
                  setHiddenTopics(new Set(toHide))
                }}
                className="h-7 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
              >
                Top 5 anzeigen
              </button>

              {gapNotes.length > 0 && (
                <p className="flex items-center gap-1.5 text-[11px] text-slate-500 italic">
                  <span className="inline-block w-5 h-0 border-t border-dashed border-slate-400"></span>
                  Gestrichelte Linie = keine Bewertungen ({gapNotes.join(", ")})
                </p>
              )}

              <p className="text-[11px] text-slate-400">
                {SOURCE_LABEL[source]} · {GRANULARITY_LABEL[granularity]}
                {granularity === "year" && selectedYear ? ` · ${selectedYear}` : ""}
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
})
