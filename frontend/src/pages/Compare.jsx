import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    LineChart,
    Line,
    RadarChart,
    Radar,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
} from "recharts"
import { Building2, Plus, X, ArrowLeft, Loader2, TrendingUp, TrendingDown, Minus, AlertTriangle, ThumbsDown, Download, Palette, Trophy, BarChart3 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { exportCompareAsPDF } from "@/utils/pdfExport"
import { Compare as CompareIcon, Star as StarIcon, Tag, TrendUp as TrendUpIcon } from "../icons"
import { API_URL } from "../config"

/* ─── Design-System Section component ─── */
function DSSection({ icon, eyebrow, title, action, children, className = "" }) {
  return (
    <section className={`bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs ${className}`}>
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
        {action && <div className="flex-shrink-0" onClick={(e) => e.stopPropagation()}>{action}</div>}
      </header>
      <div className="p-4">{children}</div>
    </section>
  )
}

// Color palette for company selection
const COLOR_PALETTE = [
    { hex: "#3b82f6", label: "Blau",    bg: "bg-blue-50",    border: "border-blue-200",    text: "text-blue-700" },
    { hex: "#f59e0b", label: "Amber",   bg: "bg-amber-50",   border: "border-amber-200",   text: "text-amber-700" },
    { hex: "#10b981", label: "Grün",    bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700" },
    { hex: "#ef4444", label: "Rot",     bg: "bg-red-50",     border: "border-red-200",     text: "text-red-700" },
    { hex: "#8b5cf6", label: "Violett", bg: "bg-violet-50",  border: "border-violet-200",  text: "text-violet-700" },
    { hex: "#ec4899", label: "Pink",    bg: "bg-pink-50",    border: "border-pink-200",    text: "text-pink-700" },
    { hex: "#06b6d4", label: "Cyan",    bg: "bg-cyan-50",    border: "border-cyan-200",    text: "text-cyan-700" },
    { hex: "#f97316", label: "Orange",  bg: "bg-orange-50",  border: "border-orange-200",  text: "text-orange-700" },
    { hex: "#14b8a6", label: "Teal",    bg: "bg-teal-50",    border: "border-teal-200",    text: "text-teal-700" },
    { hex: "#6366f1", label: "Indigo",  bg: "bg-indigo-50",  border: "border-indigo-200",  text: "text-indigo-700" },
]

const DEFAULT_COLOR_INDICES = [0, 1, 2] // blue, amber, green

const MONTH_NAMES = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

// Fill in missing months and create per-slot gap (interpolated) series for dashed line display
function processTimelineOverlayWithGaps(timelineOverlay, activeSlots) {
    if (!timelineOverlay?.length || !activeSlots?.length) return { data: [], slotHasGaps: {} }

    const parseKey = (key) => {
        const [y, m] = (key || '').split('-').map(Number)
        return { year: y, month: m }
    }
    const toKey = (year, month) => `${year}-${String(month).padStart(2, '0')}`

    const sorted = [...new Set(timelineOverlay.map((r) => r.dateKey).filter(Boolean))].sort()
    if (sorted.length === 0) return { data: timelineOverlay, slotHasGaps: {} }

    const first = parseKey(sorted[0])
    const last = parseKey(sorted[sorted.length - 1])
    const fullMonths = []
    let y = first.year
    let m = first.month
    while (y < last.year || (y === last.year && m <= last.month)) {
        fullMonths.push({
            key: toKey(y, m),
            year: y,
            monthNum: m,
            date_display: `${MONTH_NAMES[m - 1]} ${y}`,
        })
        m++
        if (m > 12) {
            m = 1
            y++
        }
    }

    const rowByKey = {}
    timelineOverlay.forEach((row) => {
        const k = row.dateKey
        if (k) rowByKey[k] = row
    })

    const data = fullMonths.map(({ key, date_display }) => {
        const existing = rowByKey[key] || {}
        const row = {
            date: date_display,
            dateKey: key,
            _slotMissing: {},
        }
        activeSlots.forEach((slot) => {
            const val = existing[slot.name]
            row[slot.name] = val != null ? val : null
            if (val == null) row._slotMissing[slot.name] = true
        })
        return row
    })

    const slotHasGaps = {}
    activeSlots.forEach((slot) => {
        slotHasGaps[slot.name] = data.some((row) => row._slotMissing[slot.name])
    })

    // Per-slot interpolation for gap series (slot.name + 'Gap')
    activeSlots.forEach((slot) => {
        const key = slot.name + 'Gap'
        data.forEach((row) => {
            row[key] = null
        })
        let i = 0
        while (i < data.length) {
            if (!data[i]._slotMissing[slot.name]) {
                i++
                continue
            }
            const gapStart = i
            let gapEnd = i
            while (gapEnd < data.length && data[gapEnd]._slotMissing[slot.name]) gapEnd++
            const beforeIdx = gapStart - 1
            const afterIdx = gapEnd
            if (
                beforeIdx >= 0 &&
                afterIdx < data.length &&
                data[beforeIdx][slot.name] != null &&
                data[afterIdx][slot.name] != null
            ) {
                const beforeVal = data[beforeIdx][slot.name]
                const afterVal = data[afterIdx][slot.name]
                const totalLen = afterIdx - beforeIdx
                data[beforeIdx][key] = beforeVal
                data[afterIdx][key] = afterVal
                for (let j = gapStart; j < gapEnd; j++) {
                    const t = (j - beforeIdx) / totalLen
                    data[j][key] = +(beforeVal + t * (afterVal - beforeVal)).toFixed(2)
                }
            }
            i = gapEnd
        }
    })

    return { data, slotHasGaps }
}

const CATEGORY_LABELS = {
    avg_arbeitsatmosphaere: "Arbeitsatmosphäre",
    avg_image: "Image",
    avg_work_life_balance: "Work-Life-Balance",
    avg_karriere_weiterbildung: "Karriere/Weiterbildung",
    avg_gehalt_sozialleistungen: "Gehalt/Sozialleistungen",
    avg_kollegenzusammenhalt: "Kollegenzusammenhalt",
    avg_umwelt_sozialbewusstsein: "Umwelt-/Sozialbewusstsein",
    avg_vorgesetztenverhalten: "Vorgesetztenverhalten",
    avg_kommunikation: "Kommunikation",
    avg_interessante_aufgaben: "Interessante Aufgaben",
    avg_umgang_aelteren_kollegen: "Umgang m. ä. Kollegen",
    avg_arbeitsbedingungen: "Arbeitsbedingungen",
    avg_gleichberechtigung: "Gleichberechtigung",
}
// Map tooltip label back to category key for per-category counts
const LABEL_TO_CATEGORY_KEY = Object.fromEntries(
    Object.entries(CATEGORY_LABELS).map(([key, label]) => [label, key])
)

const MAX_COMPANIES = 3

const ComparePage = () => {
    const location = useLocation()
    const navigate = useNavigate()

    // Each slot: { id, name, query, colorIndex }
    const initialCompanies = location.state?.companies ?? []
    const [slots, setSlots] = useState(() => {
        const initial = initialCompanies.map((c, i) => ({
            id: c.id != null ? String(c.id) : null,
            name: c.name ?? "",
            query: c.name ?? "",
            colorIndex: DEFAULT_COLOR_INDICES[i] ?? i % COLOR_PALETTE.length,
        }))
        // Always start with at least 2 slots
        while (initial.length < 2) {
            initial.push({ id: null, name: "", query: "", colorIndex: DEFAULT_COLOR_INDICES[initial.length] ?? initial.length % COLOR_PALETTE.length })
        }
        return initial
    })

    // Color picker popover state
    const [colorPickerSlot, setColorPickerSlot] = useState(null)
    const colorPickerRef = useRef(null)

    // Toggle between radar and bar chart in category comparison card
    const [categoryChartView, setCategoryChartView] = useState("radar")

    // Close color picker when clicking outside
    useEffect(() => {
        if (colorPickerSlot === null) return
        const handleClickOutside = (e) => {
            if (colorPickerRef.current && !colorPickerRef.current.contains(e.target)) {
                setColorPickerSlot(null)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [colorPickerSlot])

    // Per-company data keyed by company id
    const [companyData, setCompanyData] = useState({})
    const [loadingIds, setLoadingIds] = useState(new Set())

    // ---------- Slot management ----------
    const updateSlotQuery = (index, value) => {
        setSlots((prev) => {
            const next = [...prev]
            next[index] = { ...next[index], query: value, id: null, name: "" }
            return next
        })
    }

    const selectCompanyForSlot = (index, company) => {
        if (!company) return
        // Prevent selecting a company already in another slot
        const alreadySelected = slots.some(
            (s, i) => i !== index && s.id === String(company.id)
        )
        if (alreadySelected) return

        setSlots((prev) => {
            const next = [...prev]
            next[index] = {
                ...next[index],
                id: String(company.id),
                name: company.name,
                query: company.name,
            }
            return next
        })
    }

    const clearSlot = (index) => {
        setSlots((prev) => {
            const next = [...prev]
            if (next.length > 2) {
                // Remove slot entirely if more than 2
                next.splice(index, 1)
            } else {
                // Just clear the slot
                next[index] = { ...next[index], id: null, name: "", query: "" }
            }
            return next
        })
    }

    const addSlot = () => {
        if (slots.length >= MAX_COMPANIES) return
        setSlots((prev) => {
            // Pick a color not already used
            const usedColors = prev.map(s => s.colorIndex)
            const available = DEFAULT_COLOR_INDICES.find(ci => !usedColors.includes(ci)) 
                ?? COLOR_PALETTE.findIndex((_, i) => !usedColors.includes(i))
            return [...prev, { id: null, name: "", query: "", colorIndex: available >= 0 ? available : prev.length }]
        })
    }

    const updateSlotColor = (slotIndex, newColorIndex) => {
        setSlots((prev) => {
            const next = [...prev]
            next[slotIndex] = { ...next[slotIndex], colorIndex: newColorIndex }
            return next
        })
        setColorPickerSlot(null)
    }

    // Helper to get color info for a slot
    const getSlotColor = (slotIndex) => COLOR_PALETTE[slots[slotIndex]?.colorIndex ?? 0] || COLOR_PALETTE[0]

    // ---------- Data fetching ----------
    const fetchCompanyData = useCallback(async (companyId) => {
        if (!companyId || companyData[companyId]) return

        setLoadingIds((prev) => new Set(prev).add(companyId))

        try {
            const [ratingsRes, avgRes, trendRes, timelineRes, overviewRes, negTopicsRes, categoryCountsRes] =
                await Promise.allSettled([
                    fetch(`${API_URL}/companies/${companyId}/ratings`),
                    fetch(`${API_URL}/companies/${companyId}/ratings/avg`),
                    fetch(
                        `${API_URL}/companies/${companyId}/ratings/trend?mode=stable_all&months=12`
                    ),
                    fetch(
                        `${API_URL}/analytics/company/${companyId}/timeline?days=1825&forecast_months=0&source=employee`
                    ),
                    fetch(
                        `${API_URL}/analytics/company/${companyId}/overview`
                    ),
                    fetch(
                        `${API_URL}/topics/company/${companyId}/negative-topics`
                    ),
                    fetch(
                        `${API_URL}/companies/${companyId}/ratings/category-counts`
                    ),
                ])

            const ratings =
                ratingsRes.status === "fulfilled" && ratingsRes.value.ok
                    ? await ratingsRes.value.json()
                    : null
            const avg =
                avgRes.status === "fulfilled" && avgRes.value.ok
                    ? await avgRes.value.json()
                    : null
            const trendJson =
                trendRes.status === "fulfilled" && trendRes.value.ok
                    ? await trendRes.value.json()
                    : null
            const timelineJson =
                timelineRes.status === "fulfilled" && timelineRes.value.ok
                    ? await timelineRes.value.json()
                    : null
            const overviewJson =
                overviewRes.status === "fulfilled" && overviewRes.value.ok
                    ? await overviewRes.value.json()
                    : null
            const categoryCountsJson =
                categoryCountsRes.status === "fulfilled" && categoryCountsRes.value.ok
                    ? await categoryCountsRes.value.json()
                    : null
            const negTopicsJson =
                negTopicsRes.status === "fulfilled" && negTopicsRes.value.ok
                    ? await negTopicsRes.value.json()
                    : null

            // Parse trend
            let trend = null
            if (trendJson) {
                const deltaRaw =
                    trendJson.overall?.deltaPoints ?? trendJson.overall?.avgDelta
                const delta =
                    typeof deltaRaw === "number"
                        ? deltaRaw
                        : parseFloat(deltaRaw)
                if (Number.isFinite(delta)) {
                    const rounded = Math.round(delta * 10) / 10
                    let sign = "flat"
                    if (rounded > 0.05) sign = "up"
                    else if (rounded < -0.05) sign = "down"
                    trend = { avgDelta: rounded.toFixed(1), sign, windowMonths: trendJson.months ?? null }
                }
            }

            // Parse most critical category (lowest rated)
            let mostCritical = null
            if (avg && typeof avg === "object") {
                const entries = Object.entries(avg)
                    .map(([key, value]) => ({
                        key,
                        title: CATEGORY_LABELS[key] ?? key,
                        score: Number(value),
                    }))
                    .filter((x) => CATEGORY_LABELS[x.key] && Number.isFinite(x.score))
                if (entries.length) {
                    const min = entries.reduce((best, cur) =>
                        cur.score < best.score ? cur : best, entries[0]
                    )
                    mostCritical = { topicName: min.title, score: min.score.toFixed(2) }
                }
            }

            // Parse negative topic (highest impact = mentions × (5 - rating))
            let negativeTopic = null
            const negList = negTopicsJson?.negative_topics || []
            if (Array.isArray(negList) && negList.length) {
                const mentionsOf = (t) => { const n = Number(t?.mention_count); return Number.isFinite(n) ? n : 0 }
                const ratingOf = (t) => { const r = Number(t?.avg_rating); return Number.isFinite(r) ? r : NaN }
                const impactOf = (t) => { const r = ratingOf(t); return Number.isFinite(r) ? Math.max(0, mentionsOf(t)) * Math.max(0, 5 - r) : 0 }
                const chosen = negList.reduce((best, cur) => {
                    const bi = impactOf(best), ci = impactOf(cur)
                    if (ci > bi) return cur
                    if (ci < bi) return best
                    const br = ratingOf(best), cr = ratingOf(cur)
                    if (Number.isFinite(br) && Number.isFinite(cr)) {
                        if (cr < br) return cur
                        if (cr > br) return best
                    }
                    return mentionsOf(cur) > mentionsOf(best) ? cur : best
                }, negList[0])
                negativeTopic = {
                    ...chosen,
                    topic_label: chosen?.topic_label || chosen?.topic || chosen?.topic_text,
                }
            }

            // Fallback: use topic-overview if negative-topics returned nothing
            if (!negativeTopic) {
                try {
                    const fallbackRes = await fetch(`${API_URL}/analytics/company/${companyId}/topic-overview`)
                    if (fallbackRes.ok) {
                        const fallbackJson = await fallbackRes.json()
                        const topics = Array.isArray(fallbackJson?.topics) ? fallbackJson.topics : []
                        if (topics.length) {
                            const normSent = (s) => String(s || "").toLowerCase()
                            const isNeg = (t) => normSent(t?.sentiment).includes("neg")
                            const isNeu = (t) => normSent(t?.sentiment).includes("neu")
                            const isPos = (t) => normSent(t?.sentiment).includes("pos")
                            const hasNoSentiment = (t) => !normSent(t?.sentiment)
                            const ratingOf = (t) => { const r = Number(t?.avgRating); return Number.isFinite(r) ? r : NaN }
                            const freqOf = (t) => { const f = Number(t?.frequency); return Number.isFinite(f) ? f : 0 }

                            const negativeOnly = topics.filter(isNeg)
                            const neutralOnly = topics.filter(isNeu)
                            const noSentimentOnly = topics.filter(hasNoSentiment)
                            const basePool = negativeOnly.length
                                ? negativeOnly
                                : (neutralOnly.length ? neutralOnly : (noSentimentOnly.length ? noSentimentOnly : topics.filter((t) => !isPos(t))))

                            const withRating = basePool.filter((t) => Number.isFinite(ratingOf(t)))
                            const ratingPool = withRating.length ? withRating : basePool

                            if (ratingPool.length) {
                                const impactOf = (t) => {
                                    const f = Math.max(0, freqOf(t))
                                    const r = ratingOf(t)
                                    if (!Number.isFinite(r)) return 0
                                    return f * Math.max(0, 5 - r)
                                }
                                const chosen = ratingPool.reduce((best, cur) => {
                                    const bi = impactOf(best), ci = impactOf(cur)
                                    if (ci > bi) return cur
                                    if (ci < bi) return best
                                    const br = ratingOf(best), cr = ratingOf(cur)
                                    if (Number.isFinite(br) && Number.isFinite(cr)) {
                                        if (cr < br) return cur
                                        if (cr > br) return best
                                    }
                                    return freqOf(cur) > freqOf(best) ? cur : best
                                }, ratingPool[0])
                                negativeTopic = {
                                    ...chosen,
                                    topic_label: chosen?.topic || chosen?.topic_label,
                                }
                            }
                        }
                    }
                } catch (_) { /* ignore fallback errors */ }
            }

            setCompanyData((prev) => ({
                ...prev,
                [companyId]: {
                    ratings,
                    categoryRatings: avg,
                    categoryCounts: categoryCountsJson ?? {},
                    trend,
                    mostCritical,
                    negativeTopic,
                    timeline: timelineJson?.timeline ?? [],
                    overview: overviewJson,
                },
            }))
        } catch (err) {
            console.error("Error fetching data for company", companyId, err)
        } finally {
            setLoadingIds((prev) => {
                const next = new Set(prev)
                next.delete(companyId)
                return next
            })
        }
    }, [companyData])

    // Fetch data when slots change
    useEffect(() => {
        slots.forEach((slot) => {
            if (slot.id) fetchCompanyData(slot.id)
        })
    }, [slots, fetchCompanyData])

    // ---------- Derived data ----------
    const activeSlots = slots.filter((s) => s.id && companyData[s.id])

    // Build radar chart data
    const radarData = Object.entries(CATEGORY_LABELS).map(([key, label]) => {
        const point = { category: label }
        activeSlots.forEach((slot) => {
            const val = companyData[slot.id]?.categoryRatings?.[key]
            point[slot.name] = val != null ? Number(Number(val).toFixed(2)) : 0
        })
        return point
    })

    // Build bar chart data (same data, different view)
    const barData = radarData

    // Per-category rating count per company (for tooltips): from categoryCounts API
    const categoryCountByCompanyAndCategory = {}
    activeSlots.forEach((slot) => {
        categoryCountByCompanyAndCategory[slot.name] = companyData[slot.id]?.categoryCounts ?? {}
    })

    // Custom tooltip for category charts: shows value + number of ratings for this category per company
    const CategoryChartTooltip = ({ active, payload, label }) => {
        if (!active || !payload?.length || !label) return null
        const categoryKey = LABEL_TO_CATEGORY_KEY[label]
        return (
            <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md">
                <p className="mb-1.5 font-semibold text-slate-800">{label}</p>
                <ul className="space-y-1">
                    {payload.map((entry) => {
                        const count = categoryKey
                            ? (categoryCountByCompanyAndCategory[entry.name]?.[categoryKey] ?? 0)
                            : 0
                        return (
                            <li key={entry.name} className="flex items-center gap-2 text-sm">
                                <span
                                    className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                                    style={{ backgroundColor: entry.color }}
                                />
                                <span className="text-slate-700">
                                    {entry.name}: {entry.value != null ? Number(entry.value).toFixed(2) : "–"}
                                </span>
                                <span className="text-slate-500">
                                    ({count} Bewertung{count !== 1 ? "en" : ""})
                                </span>
                            </li>
                        )
                    })}
                </ul>
            </div>
        )
    }

    // Build timeline overlay data (with dateKey for gap processing)
    const buildTimelineOverlay = () => {
        const monthMap = {}
        const monthOrder = []
        activeSlots.forEach((slot) => {
            const timeline = companyData[slot.id]?.timeline ?? []
            timeline.forEach((entry) => {
                if (!entry.date || entry.is_forecast) return
                if (!monthMap[entry.date]) {
                    monthMap[entry.date] = {
                        dateKey: entry.date,
                        date: entry.date_display || entry.date,
                    }
                    monthOrder.push(entry.date)
                }
                monthMap[entry.date][slot.name] = entry.score
            })
        })
        return monthOrder
            .sort()
            .map((key) => monthMap[key])
    }

    const rawTimelineOverlay = buildTimelineOverlay()
    const { data: timelineOverlay, slotHasGaps } = processTimelineOverlayWithGaps(rawTimelineOverlay, activeSlots)

    const getNegativeTopicName = (t) => {
        if (!t) return "–"
        if (t.topic_label) return String(t.topic_label)
        if (t.topic_text) return String(t.topic_text)
        if (t.topic) return String(t.topic)
        if (Array.isArray(t.topic_words) && t.topic_words.length) return String(t.topic_words[0])
        if (Array.isArray(t.categories) && t.categories.length) return String(t.categories[0])
        return "–"
    }

    // ---------- Summary insights (Zusammenfassung) ----------
    const summaryData = useMemo(() => {
        if (activeSlots.length < 2) return null

        const scores = activeSlots
            .map((slot) => ({
                name: slot.name,
                colorIndex: slot.colorIndex,
                score: companyData[slot.id]?.ratings?.avg_overall,
            }))
            .filter((s) => s.score != null && Number.isFinite(s.score))

        const maxScore = scores.length ? Math.max(...scores.map((s) => s.score)) : null
        const minScore = scores.length ? Math.min(...scores.map((s) => s.score)) : null
        const leaders = scores.filter((s) => s.score === maxScore)
        const isTied = leaders.length >= 2 && maxScore != null && minScore != null && maxScore - minScore <= 0.1
        const leader = scores.length ? { ...leaders[0], isTied } : null

        const strengths = activeSlots.map((slot) => {
            const cat = companyData[slot.id]?.categoryRatings
            if (!cat || typeof cat !== "object") return { slot, label: null, score: null }
            const entries = Object.entries(cat)
                .filter(([key]) => CATEGORY_LABELS[key] && Number.isFinite(Number(cat[key])))
                .map(([key, value]) => ({ key, label: CATEGORY_LABELS[key], score: Number(value) }))
            if (!entries.length) return { slot, label: null, score: null }
            const best = entries.reduce((a, b) => (b.score > a.score ? b : a), entries[0])
            return { slot, label: best.label, score: best.score }
        })

        const categoryKeys = Object.keys(CATEGORY_LABELS)
        const gaps = categoryKeys.map((key) => {
            const values = activeSlots
                .map((s) => companyData[s.id]?.categoryRatings?.[key])
                .filter((v) => v != null && Number.isFinite(Number(v)))
                .map(Number)
            const spread = values.length >= 2 ? Math.max(...values) - Math.min(...values) : 0
            return { key, label: CATEGORY_LABELS[key], spread, values }
        })
        const biggestGaps = gaps
            .filter((g) => g.spread > 0)
            .sort((a, b) => b.spread - a.spread)
            .slice(0, 3)

        const sharedWeaknesses = categoryKeys.filter((key) => {
            const vals = activeSlots
                .map((s) => companyData[s.id]?.categoryRatings?.[key])
                .filter((v) => v != null && Number.isFinite(Number(v)))
                .map(Number)
            return vals.length === activeSlots.length && vals.every((v) => v < 3.0)
        }).map((key) => CATEGORY_LABELS[key])

        const trends = activeSlots.map((slot) => ({
            slot,
            trend: companyData[slot.id]?.trend ?? null,
        }))

        return { leader, strengths, biggestGaps, sharedWeaknesses, trends }
    }, [activeSlots, companyData])

    const [exporting, setExporting] = useState(false)

    const handleExportPDF = async () => {
        if (activeSlots.length < 2) return
        setExporting(true)
        try {
            // Kurz warten damit Charts stabil sind
            await new Promise(r => setTimeout(r, 300))

            const companies = activeSlots.map((slot, i) => {
                const data = companyData[slot.id]
                return {
                    name: slot.name,
                    id: slot.id,
                    score: data?.ratings?.avg_overall ?? null,
                    trend: data?.trend ?? null,
                    mostCritical: data?.mostCritical ?? null,
                    negativeTopic: data?.negativeTopic ?? null,
                    categoryRatings: data?.categoryRatings ?? {},
                }
            })

            // Pass selected colors to PDF export
            const companyColors = activeSlots.map(slot => COLOR_PALETTE[slot.colorIndex]?.hex || '#3b82f6')

            await exportCompareAsPDF({
                companies,
                companyColors,
                radarChartElement: document.getElementById('compare-radar-chart-export'),
                barChartElement: document.getElementById('compare-bar-chart-export'),
                timelineChartElement: document.getElementById('compare-timeline-chart-export'),
                categoryData: radarData,
                summaryData,
                categoryChartView,
            })
        } catch (err) {
            console.error('PDF-Export fehlgeschlagen:', err)
        } finally {
            setExporting(false)
        }
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Topbar — Design-System Stil */}
            <div className="h-12 min-h-[48px] border-b border-slate-200 bg-white flex items-center px-5 gap-3 sticky top-0 z-30 flex-shrink-0">
                <button
                    onClick={() => navigate(-1)}
                    title="Zurück"
                    className="h-7 w-7 rounded-md grid place-items-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 [&_svg]:w-3.5 [&_svg]:h-3.5"
                >
                    <ArrowLeft />
                </button>
                <div className="h-5 w-px bg-slate-200" />
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                        <CompareIcon />
                    </span>
                    <div className="min-w-0">
                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                            ANALYSE · FIRMENVERGLEICH
                        </p>
                        <p className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900">
                            Vergleich · {activeSlots.length}/{MAX_COMPANIES} Firmen
                        </p>
                    </div>
                </div>
                {activeSlots.length >= 2 && (
                    <button
                        onClick={handleExportPDF}
                        disabled={exporting}
                        className={[
                            "h-8 px-3 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium border",
                            "[&_svg]:flex-none [&_svg]:w-3.5 [&_svg]:h-3.5",
                            "transition-colors",
                            exporting
                                ? "bg-slate-200 text-slate-400 border-slate-200 cursor-not-allowed"
                                : "bg-slate-900 text-white border-slate-900 hover:bg-slate-800"
                        ].join(" ")}
                    >
                        {exporting ? <Loader2 className="animate-spin" /> : <Download />}
                        {exporting ? "Exportiere…" : "PDF Export"}
                    </button>
                )}
            </div>

            <div className="flex-1 px-5 py-5 max-w-[1400px] w-full mx-auto space-y-4">

                {/* Company selectors */}
                <DSSection icon={<Building2 />} eyebrow="AUSWAHL" title="Firmen vergleichen">
                    <p className="text-[12px] text-slate-500 mb-4 -mt-1">
                        Wählen Sie bis zu {MAX_COMPANIES} Firmen aus, um sie nebeneinander zu vergleichen.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {slots.map((slot, index) => {
                                const color = getSlotColor(index)
                                return (
                                <div
                                    key={index}
                                    className={[
                                        "relative rounded-md border p-3 transition-all",
                                        slot.id
                                            ? "border-slate-200 bg-white"
                                            : "border-dashed border-slate-300 bg-slate-50",
                                    ].join(" ")}
                                >
                                    {/* Tonaler Akzentbalken links wenn besetzt */}
                                    {slot.id && (
                                        <span aria-hidden="true" className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-md" style={{ background: color.hex }} />
                                    )}
                                    {/* Header row: Color picker + label + close */}
                                    <div className="flex items-center gap-2 mb-2.5">
                                        <div className="relative" ref={colorPickerSlot === index ? colorPickerRef : null}>
                                            <button
                                                onClick={() => setColorPickerSlot(colorPickerSlot === index ? null : index)}
                                                className="w-4 h-4 rounded-full shrink-0 ring-2 ring-white shadow-sm hover:scale-110 transition-transform cursor-pointer"
                                                style={{ backgroundColor: color.hex }}
                                                title="Farbe ändern"
                                            />
                                            {colorPickerSlot === index && (
                                                <div className="absolute top-6 left-0 z-50 bg-white rounded-md shadow-lg border border-slate-200 p-2 flex gap-1.5 flex-wrap w-[170px] animate-in fade-in zoom-in-95 duration-150">
                                                    {COLOR_PALETTE.map((c, ci) => {
                                                        const usedByOther = slots.some((s, si) => si !== index && s.colorIndex === ci)
                                                        return (
                                                            <button
                                                                key={ci}
                                                                onClick={() => !usedByOther && updateSlotColor(index, ci)}
                                                                disabled={usedByOther}
                                                                className={[
                                                                    "w-6 h-6 rounded-full transition-all",
                                                                    slot.colorIndex === ci
                                                                        ? "ring-2 ring-offset-1 ring-slate-900 scale-110"
                                                                        : usedByOther
                                                                            ? "opacity-25 cursor-not-allowed"
                                                                            : "hover:scale-110 cursor-pointer",
                                                                ].join(" ")}
                                                                style={{ backgroundColor: c.hex }}
                                                                title={usedByOther ? `${c.label} (vergeben)` : c.label}
                                                            />
                                                        )
                                                    })}
                                                </div>
                                            )}
                                        </div>
                                        <span className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">
                                            FIRMA {index + 1}
                                        </span>
                                        {slot.id && (
                                            <button
                                                onClick={() => clearSlot(index)}
                                                className="ml-auto h-6 w-6 rounded-md grid place-items-center text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                                                title="Firma entfernen"
                                            >
                                                <X className="h-3.5 w-3.5" />
                                            </button>
                                        )}
                                    </div>

                                    {slot.id ? (
                                        <div className="flex items-center gap-2 min-h-[28px]">
                                            <Building2 className="h-4 w-4 text-slate-400 flex-none" />
                                            <span className="text-[13px] font-semibold text-slate-900 truncate">
                                                {slot.name}
                                            </span>
                                            {loadingIds.has(slot.id) && (
                                                <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400 flex-none" />
                                            )}
                                        </div>
                                    ) : (
                                        <CompanySearchSelect
                                            value={slot.query}
                                            onValueChange={(val) => updateSlotQuery(index, val)}
                                            onCompanySelect={(company) =>
                                                selectCompanyForSlot(index, company)
                                            }
                                            onCreateNew={null}
                                            variant="light"
                                            compact
                                        />
                                    )}
                                </div>
                                )
                            })}

                            {/* Add slot button */}
                            {slots.length < MAX_COMPANIES && (
                                <button
                                    onClick={addSlot}
                                    className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-slate-300 p-4 text-slate-500 hover:text-slate-900 hover:bg-slate-50 hover:border-slate-400 transition-all min-h-[100px]"
                                >
                                    <Plus className="h-5 w-5" />
                                    <span className="text-[12px] font-medium">Firma hinzufügen</span>
                                </button>
                            )}
                        </div>
                </DSSection>

                {/* Show content only when at least 2 companies selected */}
                {activeSlots.length < 2 ? (
                    <div className="bg-white border border-slate-200 rounded-lg shadow-xs flex flex-col items-center justify-center py-20 gap-3">
                        <span className="w-14 h-14 rounded-full grid place-items-center bg-slate-100 text-slate-400 [&_svg]:w-7 [&_svg]:h-7">
                            <CompareIcon />
                        </span>
                        <div className="text-center">
                            <p className="text-[14px] font-semibold text-slate-700 m-0">
                                Mindestens 2 Firmen auswählen
                            </p>
                            <p className="text-[12px] text-slate-500 mt-1 m-0">
                                Wählen Sie oben mindestens zwei Firmen, um den Vergleich zu starten.
                            </p>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* KPI Cards comparison */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {/* Ø Score comparison */}
                            <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                                <CardHeader className="px-4 py-3 border-b border-slate-200">
                                    <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                        Ø Score
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-4 space-y-3">
                                    {activeSlots.map((slot, i) => {
                                        const score =
                                            companyData[slot.id]?.ratings?.avg_overall
                                        return (
                                            <div
                                                key={slot.id}
                                                className="flex items-center justify-between"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <div
                                                        className="w-2.5 h-2.5 rounded-full"
                                                        style={{
                                                            backgroundColor:
                                                                COLOR_PALETTE[slot.colorIndex]?.hex,
                                                        }}
                                                    />
                                                    <span className="text-sm font-medium text-slate-700 truncate max-w-[120px]">
                                                        {slot.name}
                                                    </span>
                                                </div>
                                                <span
                                                    className={`text-xl font-extrabold ${
                                                        score >= 3.5
                                                            ? "text-green-600"
                                                            : score >= 2.5
                                                            ? "text-slate-800"
                                                            : score != null
                                                            ? "text-red-500"
                                                            : "text-slate-400"
                                                    }`}
                                                >
                                                    {score != null ? score : "–"}
                                                </span>
                                            </div>
                                        )
                                    })}
                                </CardContent>
                            </Card>

                            {/* Trend comparison */}
                            <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                                <CardHeader className="px-4 py-3 border-b border-slate-200">
                                    <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                        Trend
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-4 space-y-3">
                                    {activeSlots.map((slot, i) => {
                                        const trend = companyData[slot.id]?.trend
                                        return (
                                            <div
                                                key={slot.id}
                                                className="flex items-center justify-between"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <div
                                                        className="w-2.5 h-2.5 rounded-full"
                                                        style={{
                                                            backgroundColor:
                                                                COLOR_PALETTE[slot.colorIndex]?.hex,
                                                        }}
                                                    />
                                                    <span className="text-sm font-medium text-slate-700 truncate max-w-[120px]">
                                                        {slot.name}
                                                    </span>
                                                </div>
                                                {trend ? (
                                                    <div className="flex items-center gap-1.5">
                                                        {trend.sign === "up" ? (
                                                            <TrendingUp className="h-4 w-4 text-green-600" />
                                                        ) : trend.sign === "down" ? (
                                                            <TrendingDown className="h-4 w-4 text-red-600" />
                                                        ) : (
                                                            <Minus className="h-4 w-4 text-slate-400" />
                                                        )}
                                                        <span
                                                            className={`text-lg font-extrabold ${
                                                                trend.sign === "up"
                                                                    ? "text-green-600"
                                                                    : trend.sign === "down"
                                                                    ? "text-red-600"
                                                                    : "text-slate-500"
                                                            }`}
                                                        >
                                                            {parseFloat(trend.avgDelta) > 0
                                                                ? "+"
                                                                : ""}
                                                            {trend.avgDelta}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span className="text-slate-400 font-bold">
                                                        –
                                                    </span>
                                                )}
                                            </div>
                                        )
                                    })}
                                </CardContent>
                            </Card>

                            {/* Most Critical comparison */}
                            <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                                <CardHeader className="px-4 py-3 border-b border-slate-200">
                                    <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                        Most Critical
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-4 space-y-3">
                                    {activeSlots.map((slot, i) => {
                                        const mc = companyData[slot.id]?.mostCritical
                                        return (
                                            <div key={slot.id} className="space-y-0.5">
                                                <div className="flex items-center gap-1.5">
                                                    <div
                                                        className="w-2.5 h-2.5 rounded-full shrink-0"
                                                        style={{
                                                            backgroundColor:
                                                                COLOR_PALETTE[slot.colorIndex]?.hex,
                                                        }}
                                                    />
                                                    <span className="text-xs font-medium text-slate-500 truncate" title={slot.name}>
                                                        {slot.name}
                                                    </span>
                                                </div>
                                                <div className="pl-4">
                                                    <div
                                                        className="text-sm font-bold text-red-600 leading-snug [overflow-wrap:anywhere]"
                                                        title={mc?.topicName}
                                                    >
                                                        {mc ? mc.topicName : "–"}
                                                    </div>
                                                    {mc && (
                                                        <div className="text-xs font-semibold text-red-500">
                                                            {mc.score}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )
                                    })}
                                </CardContent>
                            </Card>

                            {/* Negative Topic comparison */}
                            <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                                <CardHeader className="px-4 py-3 border-b border-slate-200">
                                    <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                        Negative Topic
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-4 space-y-3">
                                    {activeSlots.map((slot, i) => {
                                        const nt = companyData[slot.id]?.negativeTopic
                                        const ntName = getNegativeTopicName(nt)
                                        return (
                                            <div key={slot.id} className="space-y-0.5">
                                                <div className="flex items-center gap-1.5">
                                                    <div
                                                        className="w-2.5 h-2.5 rounded-full shrink-0"
                                                        style={{
                                                            backgroundColor:
                                                                COLOR_PALETTE[slot.colorIndex]?.hex,
                                                        }}
                                                    />
                                                    <span className="text-xs font-medium text-slate-500 truncate" title={slot.name}>
                                                        {slot.name}
                                                    </span>
                                                </div>
                                                <div
                                                    className="pl-4 text-sm font-extrabold text-orange-400 leading-snug [overflow-wrap:anywhere]"
                                                    title={ntName}
                                                >
                                                    {ntName}
                                                </div>
                                            </div>
                                        )
                                    })}
                                </CardContent>
                            </Card>
                        </div>

                        {/* Zusammenfassung (Summary) */}
                        {summaryData && (
                            <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                                <CardHeader className="px-4 py-3 border-b border-slate-200">
                                    <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                        Zusammenfassung
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {/* Gesamtführer */}
                                        <div className="flex gap-3">
                                            <div className="shrink-0 w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center">
                                                <Trophy className="h-4 w-4 text-amber-600" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-semibold text-slate-800 mb-1">Gesamtführer</p>
                                                {summaryData.leader ? (
                                                    summaryData.leader.isTied ? (
                                                        <p className="text-sm text-slate-600">Mehrere Firmen gleichauf (Ø {Number(summaryData.leader.score).toFixed(2)})</p>
                                                    ) : (
                                                        <p className="text-sm text-slate-600 flex items-center gap-1.5">
                                                            <span className="inline-block w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLOR_PALETTE[summaryData.leader.colorIndex]?.hex }} />
                                                            {summaryData.leader.name}: {Number(summaryData.leader.score).toFixed(2)}
                                                        </p>
                                                    )
                                                ) : (
                                                    <p className="text-sm text-slate-500">–</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Stärken-Profil */}
                                        <div className="flex gap-3">
                                            <div className="shrink-0 w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center">
                                                <TrendingUp className="h-4 w-4 text-emerald-600" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-semibold text-slate-800 mb-1">Stärken-Profil</p>
                                                <ul className="space-y-0.5">
                                                    {summaryData.strengths.map(({ slot, label, score }) => (
                                                        <li key={slot.id} className="text-sm text-slate-600 flex items-center gap-1.5">
                                                            <span className="inline-block w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLOR_PALETTE[slot.colorIndex]?.hex }} />
                                                            {slot.name}: {label ?? "–"}{score != null ? ` (${score.toFixed(2)})` : ""}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>

                                        {/* Größte Unterschiede */}
                                        <div className="flex gap-3">
                                            <div className="shrink-0 w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
                                                <BarChart3 className="h-4 w-4 text-blue-600" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-semibold text-slate-800 mb-1">Größte Unterschiede</p>
                                                {summaryData.biggestGaps.length ? (
                                                    <ul className="space-y-0.5 text-sm text-slate-600">
                                                        {summaryData.biggestGaps.map((g) => (
                                                            <li key={g.key}>{g.label}: Differenz {g.spread.toFixed(2)} Punkte</li>
                                                        ))}
                                                    </ul>
                                                ) : (
                                                    <p className="text-sm text-slate-500">Keine nennenswerten Unterschiede</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Gemeinsame Schwächen */}
                                        <div className="flex gap-3 md:col-span-2 lg:col-span-1">
                                            <div className="shrink-0 w-9 h-9 rounded-lg bg-red-100 flex items-center justify-center">
                                                <AlertTriangle className="h-4 w-4 text-red-600" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-semibold text-slate-800 mb-1">Gemeinsame Schwächen</p>
                                                {summaryData.sharedWeaknesses.length ? (
                                                    <p className="text-sm text-slate-600">{summaryData.sharedWeaknesses.join(", ")} (alle unter 3,0)</p>
                                                ) : (
                                                    <p className="text-sm text-slate-600">Keine – keine Kategorie bei allen unter 3,0</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Trend-Ausblick */}
                                        <div className="flex gap-3 md:col-span-2">
                                            <div className="shrink-0 w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                                                <TrendingUp className="h-4 w-4 text-slate-600" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-semibold text-slate-800 mb-1">Trend-Ausblick</p>
                                                <ul className="space-y-0.5">
                                                    {summaryData.trends.map(({ slot, trend }) => (
                                                        <li key={slot.id} className="text-sm text-slate-600 flex items-center gap-2">
                                                            <span className="inline-block w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLOR_PALETTE[slot.colorIndex]?.hex }} />
                                                            {slot.name}:
                                                            {trend ? (
                                                                <>
                                                                    {trend.sign === "up" && <TrendingUp className="h-3.5 w-3.5 text-green-600 inline" />}
                                                                    {trend.sign === "down" && <TrendingDown className="h-3.5 w-3.5 text-red-600 inline" />}
                                                                    {trend.sign === "flat" && <Minus className="h-3.5 w-3.5 text-slate-400 inline" />}
                                                                    <span className={trend.sign === "up" ? "text-green-600" : trend.sign === "down" ? "text-red-600" : "text-slate-500"}>
                                                                        {parseFloat(trend.avgDelta) > 0 ? "+" : ""}{trend.avgDelta}{trend.windowMonths ? ` (${trend.windowMonths} Mon.)` : ""}
                                                                    </span>
                                                                </>
                                                            ) : (
                                                                <span className="text-slate-400">–</span>
                                                            )}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Category Ratings comparison - Radar / Bar charts in one card with toggle */}
                        <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                            <CardHeader className="px-4 py-3 border-b border-slate-200 flex flex-row items-center justify-between space-y-0">
                                <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                    Kategorievergleich
                                </CardTitle>
                                <div className="flex rounded-lg border border-slate-200 bg-slate-100/80 p-0.5">
                                    <button
                                        type="button"
                                        onClick={() => setCategoryChartView("radar")}
                                        className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                                            categoryChartView === "radar"
                                                ? "bg-white text-slate-800 shadow-sm"
                                                : "text-slate-600 hover:text-slate-800"
                                        }`}
                                    >
                                        Radar
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setCategoryChartView("bar")}
                                        className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                                            categoryChartView === "bar"
                                                ? "bg-white text-slate-800 shadow-sm"
                                                : "text-slate-600 hover:text-slate-800"
                                        }`}
                                    >
                                        Balken
                                    </button>
                                </div>
                            </CardHeader>
                            <CardContent className="p-4">
                                <div
                                    id="compare-radar-chart-export"
                                    className={categoryChartView === "radar" ? "block" : "hidden"}
                                >
                                    <ResponsiveContainer width="100%" height={400}>
                                        <RadarChart
                                            data={radarData}
                                            cx="50%"
                                            cy="50%"
                                            outerRadius="70%"
                                        >
                                            <PolarGrid stroke="#e2e8f0" />
                                            <PolarAngleAxis
                                                dataKey="category"
                                                tick={{ fontSize: 11, fill: "#64748b" }}
                                            />
                                            <PolarRadiusAxis
                                                domain={[0, 5]}
                                                tick={{ fontSize: 10, fill: "#94a3b8" }}
                                            />
                                            {activeSlots.map((slot, i) => (
                                                <Radar
                                                    key={slot.id}
                                                    name={slot.name}
                                                    dataKey={slot.name}
                                                    stroke={COLOR_PALETTE[slot.colorIndex]?.hex}
                                                    fill={COLOR_PALETTE[slot.colorIndex]?.hex}
                                                    fillOpacity={0.15}
                                                    strokeWidth={2}
                                                />
                                            ))}
                                            <Legend />
                                            <Tooltip content={<CategoryChartTooltip />} />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                                <div
                                    id="compare-bar-chart-export"
                                    className={categoryChartView === "bar" ? "block" : "hidden"}
                                >
                                    <ResponsiveContainer width="100%" height={400}>
                                        <BarChart
                                            data={barData}
                                            layout="vertical"
                                            margin={{
                                                left: 20,
                                                right: 20,
                                                top: 10,
                                                bottom: 10,
                                            }}
                                        >
                                            <CartesianGrid
                                                strokeDasharray="3 3"
                                                stroke="#f1f5f9"
                                            />
                                            <XAxis
                                                type="number"
                                                domain={[0, 5]}
                                                tick={{ fontSize: 11 }}
                                            />
                                            <YAxis
                                                type="category"
                                                dataKey="category"
                                                width={130}
                                                tick={{ fontSize: 11 }}
                                            />
                                            <Tooltip content={<CategoryChartTooltip />} />
                                            <Legend />
                                            {activeSlots.map((slot, i) => (
                                                <Bar
                                                    key={slot.id}
                                                    dataKey={slot.name}
                                                    fill={COLOR_PALETTE[slot.colorIndex]?.hex}
                                                    radius={[0, 4, 4, 0]}
                                                    barSize={activeSlots.length > 2 ? 8 : 12}
                                                />
                                            ))}
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Timeline comparison */}
                        {timelineOverlay.length > 0 && (
                            <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                                <CardHeader className="px-4 py-3 border-b border-slate-200">
                                    <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                        Bewertungsverlauf im Vergleich
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-4">
                                    <div id="compare-timeline-chart-export">
                                    <ResponsiveContainer width="100%" height={350}>
                                        <LineChart
                                            data={timelineOverlay}
                                            margin={{
                                                left: 10,
                                                right: 30,
                                                top: 10,
                                                bottom: 10,
                                            }}
                                        >
                                            <CartesianGrid
                                                strokeDasharray="3 3"
                                                stroke="#f1f5f9"
                                            />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fontSize: 11 }}
                                                interval="preserveStartEnd"
                                            />
                                            <YAxis
                                                domain={[1, 5]}
                                                tick={{ fontSize: 11 }}
                                            />
                                            <Tooltip
                                                content={({ active, payload, label }) => {
                                                    if (!active || !payload?.length || !label) return null
                                                    const point = payload[0]?.payload
                                                    const slotMissing = point?._slotMissing ?? {}
                                                    return (
                                                        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md">
                                                            <p className="mb-1.5 font-semibold text-slate-800">{label}</p>
                                                            <ul className="space-y-1">
                                                                {activeSlots.map((slot) => {
                                                                    const isMissing = slotMissing[slot.name]
                                                                    const mainVal = point?.[slot.name]
                                                                    const gapVal = point?.[slot.name + 'Gap']
                                                                    const displayVal =
                                                                        mainVal != null
                                                                            ? mainVal.toFixed(2)
                                                                            : gapVal != null
                                                                            ? gapVal.toFixed(2)
                                                                            : '–'
                                                                    const color = COLOR_PALETTE[slot.colorIndex]?.hex
                                                                    return (
                                                                        <li key={slot.id} className="flex items-center gap-2 text-sm">
                                                                            <span
                                                                                className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                                                                                style={{ backgroundColor: color }}
                                                                            />
                                                                            <span className="text-slate-700">
                                                                                {slot.name}: {displayVal}
                                                                            </span>
                                                                            {isMissing && gapVal != null && (
                                                                                <span className="text-xs text-amber-600">
                                                                                    (interpoliert)
                                                                                </span>
                                                                            )}
                                                                        </li>
                                                                    )
                                                                })}
                                                            </ul>
                                                        </div>
                                                    )
                                                }}
                                            />
                                            <Legend />
                                            {activeSlots.map((slot, i) => (
                                                <Line
                                                    key={slot.id}
                                                    type="monotone"
                                                    dataKey={slot.name}
                                                    name={slot.name}
                                                    stroke={COLOR_PALETTE[slot.colorIndex]?.hex}
                                                    strokeWidth={2.5}
                                                    dot={{ r: 3 }}
                                                    activeDot={{ r: 5 }}
                                                    connectNulls={false}
                                                />
                                            ))}
                                            {activeSlots.map((slot) =>
                                                slotHasGaps[slot.name] ? (
                                                    <Line
                                                        key={`${slot.id}-gap`}
                                                        type="monotone"
                                                        dataKey={slot.name + 'Gap'}
                                                        name={slot.name + ' (interpoliert)'}
                                                        stroke={COLOR_PALETTE[slot.colorIndex]?.hex}
                                                        strokeWidth={2}
                                                        strokeDasharray="6 4"
                                                        strokeOpacity={0.7}
                                                        dot={false}
                                                        activeDot={false}
                                                        connectNulls={false}
                                                        legendType="none"
                                                    />
                                                ) : null
                                            )}
                                        </LineChart>
                                    </ResponsiveContainer>
                                    {Object.values(slotHasGaps).some(Boolean) && (
                                        <p className="text-xs text-slate-500 text-center italic flex items-center justify-center gap-1 mt-2">
                                            <span className="inline-block w-6 h-0 border-t-2 border-dashed border-slate-400"></span>
                                            Gestrichelte Linie = Keine Daten vorhanden (interpoliert)
                                        </p>
                                    )}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Detailed category comparison table */}
                        <Card className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
                            <CardHeader className="px-4 py-3 border-b border-slate-200">
                                <CardTitle className="text-[14px] font-semibold text-slate-900 tracking-tight">
                                    Detailvergleich nach Kategorien
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b">
                                            <th className="text-left py-3 pr-4 font-semibold text-slate-600">
                                                Kategorie
                                            </th>
                                            {activeSlots.map((slot, i) => (
                                                <th
                                                    key={slot.id}
                                                    className="text-center py-3 px-4 font-semibold"
                                                >
                                                    <div className="flex items-center justify-center gap-2">
                                                        <div
                                                            className="w-2.5 h-2.5 rounded-full"
                                                            style={{
                                                                backgroundColor:
                                                                    COLOR_PALETTE[slot.colorIndex]?.hex,
                                                            }}
                                                        />
                                                        <span className="truncate max-w-[100px]">
                                                            {slot.name}
                                                        </span>
                                                    </div>
                                                </th>
                                            ))}
                                            {activeSlots.length >= 2 && (
                                                <th className="text-center py-3 px-4 font-semibold text-slate-600">
                                                    Differenz
                                                </th>
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {Object.entries(CATEGORY_LABELS).map(
                                            ([key, label]) => {
                                                const values = activeSlots.map(
                                                    (slot) => {
                                                        const v =
                                                            companyData[slot.id]
                                                                ?.categoryRatings?.[key]
                                                        return v != null
                                                            ? Number(v)
                                                            : null
                                                    }
                                                )
                                                const validValues = values.filter(
                                                    (v) => v != null
                                                )
                                                const maxVal = Math.max(...validValues)
                                                const minVal = Math.min(...validValues)
                                                const diff =
                                                    validValues.length >= 2
                                                        ? (maxVal - minVal).toFixed(2)
                                                        : null

                                                return (
                                                    <tr
                                                        key={key}
                                                        className="border-b last:border-b-0 hover:bg-slate-50 transition-colors"
                                                    >
                                                        <td className="py-3 pr-4 font-medium text-slate-700">
                                                            {label}
                                                        </td>
                                                        {values.map((val, i) => {
                                                            const isBest =
                                                                val != null &&
                                                                val === maxVal &&
                                                                validValues.length >= 2
                                                            const isWorst =
                                                                val != null &&
                                                                val === minVal &&
                                                                validValues.length >= 2 &&
                                                                maxVal !== minVal
                                                            return (
                                                                <td
                                                                    key={i}
                                                                    className={`text-center py-3 px-4 font-bold ${
                                                                        isBest
                                                                            ? "text-green-600"
                                                                            : isWorst
                                                                            ? "text-red-500"
                                                                            : "text-slate-800"
                                                                    }`}
                                                                >
                                                                    {val != null
                                                                        ? val.toFixed(2)
                                                                        : "–"}
                                                                </td>
                                                            )
                                                        })}
                                                        {activeSlots.length >= 2 && (
                                                            <td className="text-center py-3 px-4 font-semibold text-slate-500">
                                                                {diff != null
                                                                    ? `±${diff}`
                                                                    : "–"}
                                                            </td>
                                                        )}
                                                    </tr>
                                                )
                                            }
                                        )}
                                    </tbody>
                                </table>
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>
        </div>
    )
}

export default ComparePage