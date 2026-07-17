import * as React from "react"
import { useState, useEffect, useCallback, useRef } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { Loader2, Upload, Clock } from "lucide-react"

import { WorkPulseLogo }     from "@/components/WorkPulseLogo"
import { TimelineCard }      from "@/components/dashboard/TimelineCard"
import { TopicRatingCard }   from "@/components/dashboard/TopicRatingCard"
import { TopicOverviewCard } from "@/components/dashboard/TopicOverviewCard"
import KPIGrid               from "@/components/dashboard/KPIGrid"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import SorceModal        from "../components/dashboard/modals/SorceModal"
import TrendModal        from "../components/dashboard/modals/TrendModal"
import MostCriticalModal from "../components/dashboard/modals/MostCriticalModal"
import NegativTopicModal from "../components/dashboard/modals/NegativTopicModal"
import ImportModal, { getImportHistory } from "../components/dashboard/modals/ImportModal"

import {
  Dashboard as DashboardIcon, Compare, Download, Building, Home, Search, Loader, Sun, Moon,
} from "../icons"
import { useTheme } from "../hooks/useTheme"
import { API_URL } from "../config"
import { exportKPIsAsPDF } from "../utils/pdfExport"
import { waitForMultipleCharts, validateChart, waitForImagesInElement } from "../utils/chartValidator"

export default function Dashboard() {
  const location = useLocation()
  const navigate = useNavigate()
  const companyFromWelcome    = location.state?.companyId
  const companyNameFromWelcome = location.state?.companyName

  /* ---- Modal state ---- */
  const [open, setOpen]               = useState(false)
  const [openTrend, setOpenTrend]     = useState(false)
  const [openNegative, setOpenNegative] = useState(false)
  const [openMostCritical, setOpenMostCritical] = useState(false)
  const [openImport, setOpenImport]   = useState(false)

  /* ---- Import history ---- */
  const [importHistory, setImportHistory] = useState([])

  /* ---- Company state ---- */
  const [companyQuery, setCompanyQuery] = useState(companyNameFromWelcome || "")
  const [selectedCompany, setSelectedCompany]     = useState("")
  const [selectedCompanyId, setSelectedCompanyId] = useState(companyFromWelcome || null)
  const [selectedCompanyName, setSelectedCompanyName] = useState(companyNameFromWelcome || "")
  const [companies, setCompanies]   = useState([])
  const [error, setError]           = useState("")

  /* ---- KPI data ---- */
  const [data, setData]                       = useState(null)
  const [trendData, setTrendData]             = useState(null)
  const [mostCriticalData, setMostCriticalData] = useState(null)
  const [negativeTopicItem, setNegativeTopicItem] = useState(null)

  /* ---- Global time range filter ---- */
  const [globalTimeRange, setGlobalTimeRange] = useState("all")

  /* ---- Timeline / TopicRating filter state ---- */
  const [timelineFilters, setTimelineFilters] = useState({
    metric: "Ø Score", source: "employee", granularity: "overall", selectedYear: null,
  })
  const [topicRatingFilters, setTopicRatingFilters] = useState({
    source: "employee", granularity: "overall", selectedYear: null, visibleTopics: [], stats: {},
  })
  const [topicOverviewData, setTopicOverviewData] = useState({ topics: [], sourceFilter: null, stats: {} })

  /* ---- Loading ---- */
  const [dashboardLoadingStates, setDashboardLoadingStates] = useState({
    timelineChart: true, topicRatingChart: true, topicOverview: true, kpiCards: true,
  })
  const loadingStatesRef = useRef(dashboardLoadingStates)
  useEffect(() => { loadingStatesRef.current = dashboardLoadingStates }, [dashboardLoadingStates])
  const [exportingPDF, setExportingPDF] = useState(false)

  const topicOverviewRef = useRef(null)
  const debounceTimeoutRef = useRef(null)

  const effectiveCompanyId = selectedCompany || selectedCompanyId || companyFromWelcome || null

  /* ---- Company helpers ---- */
  async function getCompanies() {
    try {
      const res = await fetch(`${API_URL}/companies`)
      if (!res.ok) return
      const d = await res.json()
      setCompanies(Array.isArray(d) ? d : [])
    } catch {}
  }

  const handleCompanySelectFromDropdown = useCallback((company) => {
    if (company) {
      setSelectedCompanyId(company.id)
      setSelectedCompanyName(company.name)
      setSelectedCompany(company.id)
      setCompanyQuery(company.name)
      setError("")
    } else {
      setSelectedCompanyId(null)
      setSelectedCompanyName("")
      setSelectedCompany("")
    }
  }, [])

  const handleCreateNewCompany = (companyName) => {
    const name = companyName?.trim()
    navigate("/welcome", name ? { state: { prefillCompanyName: name } } : undefined)
  }

  function getCompanyData(id) {
    /* intentionally empty — data is loaded reactively via effectiveCompanyId useEffect */
  }

  /* ---- KPI fetching ---- */
  function getStartDate(timeRange) {
    if (timeRange === "1y") {
      const d = new Date(); d.setFullYear(d.getFullYear() - 1); return d.toISOString().slice(0, 10)
    }
    if (timeRange === "3y") {
      const d = new Date(); d.setFullYear(d.getFullYear() - 3); return d.toISOString().slice(0, 10)
    }
    return null
  }

  async function getAvg(timeRange = globalTimeRange) {
    const companyId = effectiveCompanyId
    if (!companyId) { setData(null); return }
    try {
      const startDate = getStartDate(timeRange)
      const url = startDate
        ? `${API_URL}/companies/${companyId}/ratings?start_date=${startDate}`
        : `${API_URL}/companies/${companyId}/ratings`
      const res = await fetch(url)
      if (!res.ok) throw new Error()
      setData(await res.json())
    } catch { setData(null) }
  }

  async function getTrend(timeRange = globalTimeRange) {
    const companyId = effectiveCompanyId
    if (!companyId) { setTrendData(null); return }
    const months = timeRange === "3y" ? 36 : 12
    const urls = [
      `${API_URL}/companies/${companyId}/ratings/trend?mode=stable_all&months=${months}`,
      `${API_URL}/companies/${companyId}/ratings/trend?mode=rate&days=30`,
    ]
    for (const url of urls) {
      try {
        const res = await fetch(url)
        if (!res.ok) continue
        const json = await res.json()
        const deltaRaw = json.overall?.deltaPoints ?? json.overall?.avgDelta
        const delta = typeof deltaRaw === "number" ? deltaRaw : parseFloat(deltaRaw)
        if (!Number.isFinite(delta)) continue
        const rounded = Math.round(delta * 10) / 10
        const sign = rounded > 0.05 ? "up" : rounded < -0.05 ? "down" : "flat"
        setTrendData({ avgDelta: rounded.toFixed(1), sign, windowMonths: json.months ?? null })
        return
      } catch {}
    }
    setTrendData(null)
  }

  async function getMostCritical(timeRange = globalTimeRange) {
    const companyId = effectiveCompanyId
    if (!companyId) { setMostCriticalData(null); return }
    try {
      const startDate = getStartDate(timeRange)
      const url = startDate
        ? `${API_URL}/companies/${companyId}/ratings/avg?start_date=${startDate}`
        : `${API_URL}/companies/${companyId}/ratings/avg`
      const res = await fetch(url)
      if (!res.ok) throw new Error()
      const json = await res.json()
      const labelMap = {
        avg_arbeitsatmosphaere:      "Arbeitsatmosphäre",
        avg_image:                   "Image",
        avg_work_life_balance:       "Work-Life-Balance",
        avg_karriere_weiterbildung:  "Karriere/Weiterbildung",
        avg_gehalt_sozialleistungen: "Gehalt/Sozialleistungen",
        avg_kollegenzusammenhalt:    "Kollegenzusammenhalt",
        avg_umwelt_sozialbewusstsein:"Umwelt-/Sozialbewusstsein",
        avg_vorgesetztenverhalten:   "Vorgesetztenverhalten",
        avg_kommunikation:           "Kommunikation",
        avg_interessante_aufgaben:   "Interessante Aufgaben",
        avg_umgang_aelteren_kollegen:"Umgang mit älteren Kollegen",
        avg_arbeitsbedingungen:      "Arbeitsbedingungen",
        avg_gleichberechtigung:      "Gleichberechtigung",
      }
      const entries = Object.entries(json)
        .map(([k, v]) => ({ key: k, title: labelMap[k] ?? k, score: Number(v) }))
        .filter((x) => Number.isFinite(x.score))
      if (!entries.length) { setMostCriticalData(null); return }
      const min = entries.reduce((b, c) => (c.score < b.score ? c : b), entries[0])
      setMostCriticalData({ topicName: min.title, score: min.score.toFixed(2) })
    } catch { setMostCriticalData(null) }
  }

  async function getNegativeTopic(timeRange = globalTimeRange) {
    const companyId = effectiveCompanyId
    if (!companyId) { setNegativeTopicItem(null); return }
    const startDate = getStartDate(timeRange)

    const normSent  = (s) => String(s || "").toLowerCase()
    const isNeg = (t) => normSent(t?.sentiment).includes("neg")
    const isNeu = (t) => normSent(t?.sentiment).includes("neu")
    const isPos = (t) => normSent(t?.sentiment).includes("pos")
    const hasNone = (t) => !normSent(t?.sentiment)
    const ratingOf = (t) => { const r = Number(t?.avgRating); return Number.isFinite(r) ? r : NaN }
    const freqOf   = (t) => { const f = Number(t?.frequency); return Number.isFinite(f) ? f : 0 }
    const impactOf = (t) => { const f = Math.max(0, freqOf(t)); const r = ratingOf(t); return Number.isFinite(r) ? f * Math.max(0, 5 - r) : 0 }

    const pickFromTopics = (topics) => {
      if (!topics.length) return null
      const neg = topics.filter(isNeg), neu = topics.filter(isNeu), none = topics.filter(hasNone)
      const pool = neg.length ? neg : (neu.length ? neu : (none.length ? none : topics.filter((t) => !isPos(t))))
      const rPool = pool.filter((t) => Number.isFinite(ratingOf(t)))
      const base = rPool.length ? rPool : pool
      const chosen = base.reduce((best, cur) => {
        const bi = impactOf(best), ci = impactOf(cur)
        if (ci > bi) return cur; if (ci < bi) return best
        const br = ratingOf(best), cr = ratingOf(cur)
        if (Number.isFinite(br) && Number.isFinite(cr)) { if (cr < br) return cur; if (cr > br) return best }
        return freqOf(cur) > freqOf(best) ? cur : best
      }, base[0])
      return { ...chosen, title: "Negative Topic", topic_label: chosen?.topic, categories: chosen?.topic ? [chosen.topic] : chosen?.categories }
    }

    try {
      // ML-based endpoint has no date filter — only use it for "all"
      if (!startDate) {
        const res = await fetch(`${API_URL}/topics/company/${companyId}/negative-topics`)
        if (res.ok) {
          const json = await res.json()
          const list = json?.negative_topics || []
          if (Array.isArray(list) && list.length) {
            const mentionsOf = (t) => { const n = Number(t?.mention_count); return Number.isFinite(n) ? n : 0 }
            const rOf        = (t) => { const r = Number(t?.avg_rating);    return Number.isFinite(r) ? r : NaN }
            const iOf        = (t) => { const n = Math.max(0, mentionsOf(t)); const r = rOf(t); return Number.isFinite(r) ? n * Math.max(0, 5 - r) : 0 }
            const chosen = list.reduce((best, cur) => {
              const bi = iOf(best), ci = iOf(cur)
              if (ci > bi) return cur; if (ci < bi) return best
              const br = rOf(best), cr = rOf(cur)
              if (Number.isFinite(br) && Number.isFinite(cr)) { if (cr < br) return cur; if (cr > br) return best }
              return mentionsOf(cur) > mentionsOf(best) ? cur : best
            }, list[0])
            setNegativeTopicItem({
              ...chosen,
              title: "Negative Topic",
              topic_label: chosen?.topic_label || chosen?.topic || chosen?.topic_text,
              categories: Array.isArray(chosen?.categories) ? chosen.categories : (chosen?.topic_label ? [chosen.topic_label] : []),
            })
            return
          }
        }
      }

      const fallbackUrl = startDate
        ? `${API_URL}/analytics/company/${companyId}/topic-overview?start_date=${startDate}`
        : `${API_URL}/analytics/company/${companyId}/topic-overview`
      const fallbackRes = await fetch(fallbackUrl)
      if (!fallbackRes.ok) { setNegativeTopicItem(null); return }
      const fallbackJson = await fallbackRes.json()
      const topics = Array.isArray(fallbackJson?.topics) ? fallbackJson.topics : []
      setNegativeTopicItem(pickFromTopics(topics))
    } catch { setNegativeTopicItem(null) }
  }

  const getNegativeTopicName = (t) => {
    if (!t) return "-"
    if (t.topic_label) return String(t.topic_label)
    if (t.topic_text)  return String(t.topic_text)
    if (t.topic)       return String(t.topic)
    if (Array.isArray(t.topic_words) && t.topic_words.length) return String(t.topic_words[0])
    if (Array.isArray(t.top_words) && t.top_words.length) {
      const w = t.top_words[0]
      if (typeof w === "string") return w
      if (w?.word) return String(w.word)
    }
    if (Array.isArray(t.categories) && t.categories.length) return String(t.categories[0])
    return "-"
  }

  /* ---- PDF export ---- */
  const handleExportPDF = async () => {
    if (!selectedCompanyName) { setError("Bitte wählen Sie zuerst eine Firma aus."); return }
    try {
      setExportingPDF(true); setError(null)
      const checkIfReady = () => {
        const s = loadingStatesRef.current
        return !s.timelineChart && !s.topicRatingChart && !s.topicOverview && !s.kpiCards
      }
      if (!checkIfReady()) {
        const maxWait = 45000, interval = 300, start = Date.now()
        await new Promise((resolve, reject) => {
          const t = setInterval(() => {
            if (Date.now() - start > maxWait) { clearInterval(t); reject(new Error("Timeout")); return }
            if (checkIfReady()) { clearInterval(t); resolve() }
          }, interval)
        })
      }
      const chartIds = ["timeline-chart-export", "topic-rating-chart-export"]
      const chartResults = await waitForMultipleCharts(chartIds, 15000)
      if (!chartResults.allReady) await new Promise((r) => setTimeout(r, 3000))
      const timelineEl    = document.getElementById("timeline-chart-export")
      const topicRatingEl = document.getElementById("topic-rating-chart-export")
      const tv = validateChart(timelineEl, "Timeline")
      const rv = validateChart(topicRatingEl, "Topic-Rating")
      if (!tv.isValid || !rv.isValid) {
        throw new Error("Charts nicht bereit: " + [!tv.isValid && tv.message, !rv.isValid && rv.message].filter(Boolean).join(", "))
      }
      await waitForImagesInElement(timelineEl, 3000)
      await waitForImagesInElement(topicRatingEl, 3000)
      await new Promise((r) => setTimeout(r, 1500))
      await exportKPIsAsPDF({
        companyName: selectedCompanyName,
        avgScore: data?.avg_overall || "-",
        trend: trendData,
        mostCritical: mostCriticalData,
        negativeTopic: getNegativeTopicName(negativeTopicItem),
        timelineChartElement: timelineEl,
        timelineFilters,
        topicRatingChartElement: topicRatingEl,
        topicRatingFilters,
        topicOverviewData,
      })
    } catch (err) {
      setError(`Export fehlgeschlagen: ${err.message}`)
    } finally {
      setExportingPDF(false)
    }
  }

  /* ---- Effects ---- */
  useEffect(() => {
    getCompanies()
    if (companyFromWelcome) {
      setSelectedCompany(companyFromWelcome)
      getCompanyData(companyFromWelcome)
    }
    return () => { if (debounceTimeoutRef.current) clearTimeout(debounceTimeoutRef.current) }
  }, [])

  useEffect(() => {
    if (!effectiveCompanyId) {
      setData(null); setTrendData(null); setMostCriticalData(null); setNegativeTopicItem(null)
      setDashboardLoadingStates((p) => ({ ...p, kpiCards: false }))
      setImportHistory([])
      return
    }
    setDashboardLoadingStates((p) => ({ ...p, kpiCards: true }))
    setImportHistory(getImportHistory(effectiveCompanyId))
    Promise.allSettled([getAvg(globalTimeRange), getTrend(globalTimeRange), getMostCritical(globalTimeRange), getNegativeTopic(globalTimeRange)])
      .then(() => setDashboardLoadingStates((p) => ({ ...p, kpiCards: false })))
  }, [effectiveCompanyId, globalTimeRange])

  const handleImportSuccess = useCallback(() => {
    setImportHistory(getImportHistory(effectiveCompanyId))
    Promise.allSettled([getAvg(), getTrend(), getMostCritical(), getNegativeTopic()])
      .then(() => setDashboardLoadingStates((p) => ({ ...p, kpiCards: false })))
  }, [effectiveCompanyId])

  const handleTimelineFiltersChange     = useCallback((f) => setTimelineFilters(f), [])
  const handleTimelineLoadingChange     = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, timelineChart: v })), [])
  const handleTopicRatingFiltersChange  = useCallback((f) => setTopicRatingFilters(f), [])
  const handleTopicRatingLoadingChange  = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, topicRatingChart: v })), [])
  const handleTopicOverviewDataChange   = useCallback((d) => setTopicOverviewData(d), [])
  const handleTopicOverviewLoadingChange = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, topicOverview: v })), [])

  /* ---- Theme ---- */
  const { isDark, toggle: toggleTheme } = useTheme()

  /* ================================================================
     RENDER
     ================================================================ */
  return (
    <>
      <div className="ds-app">

        {/* ---- RAIL ---- */}
        <aside className="ds-rail">
          {/* Brand */}
          <div className="ds-brand">
            <WorkPulseLogo variant="badge" />
          </div>

          {/* Analyse group */}
          <div className="ds-nav-group">
            <span className="ds-nav-group-label">Analyse</span>
            <button className="ds-nav-link active">
              <DashboardIcon />
              Dashboard
            </button>
            <button
              className="ds-nav-link"
              onClick={() => navigate("/compare", {
                state: { companies: selectedCompanyId && selectedCompanyName ? [{ id: selectedCompanyId, name: selectedCompanyName }] : [] }
              })}
            >
              <Compare />
              Vergleich
            </button>
          </div>

          {/* Daten group */}
          <div className="ds-nav-group">
            <span className="ds-nav-group-label">Daten</span>
            <button className="ds-nav-link" onClick={() => navigate("/welcome")}>
              <Building />
              Firmen
              {companies.length > 0 && (
                <span className="ds-nav-count">{companies.length}</span>
              )}
            </button>
            <button
              className="ds-nav-link"
              onClick={() => setOpenImport(true)}
              disabled={!effectiveCompanyId}
              title={effectiveCompanyId ? "Daten importieren" : "Erst eine Firma auswählen"}
            >
              <Upload style={{ width: 16, height: 16 }} />
              Importieren
            </button>
          </div>

          {/* Bottom actions */}
          <div className="ds-nav-group" style={{ marginTop: "auto" }}>
            <span className="ds-nav-group-label">Aktionen</span>
            <button className="ds-nav-link" onClick={() => navigate("/welcome")}>
              <Home />
              Startseite
            </button>
            <button
              className="ds-nav-link"
              onClick={handleExportPDF}
              disabled={exportingPDF || !effectiveCompanyId}
            >
              {exportingPDF ? <Loader /> : <Download />}
              {exportingPDF ? "Exportiere…" : "PDF Export"}
            </button>
            <button
              className="ds-nav-link"
              onClick={toggleTheme}
              title={isDark ? "Zu Hell wechseln" : "Zu Dunkel wechseln"}
            >
              {isDark ? <Sun /> : <Moon />}
              {isDark ? "Hell" : "Dunkel"}
            </button>
          </div>
        </aside>

        {/* ---- MAIN ---- */}
        <div style={{ display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--slate-0)" }}>

          {/* TOPBAR */}
          <div className="ds-topbar">
            {/* Breadcrumbs */}
            <div className="ds-crumbs">
              <span>Firmen</span>
              {selectedCompanyName && (
                <>
                  <span className="sep">/</span>
                  <span className="cur">{selectedCompanyName}</span>
                </>
              )}
            </div>

            {/* Company search */}
            <div className="ds-topbar-search">
              <Search className="ds-topbar-search-icon" width="13" height="13" />
              <CompanySearchSelect
                value={companyQuery}
                compact
                placeholder={selectedCompanyName ? "Firma wechseln…" : "Firma suchen…"}
                onValueChange={(val) => {
                  setCompanyQuery(val)
                  if (!val) {
                    setSelectedCompanyId(null)
                    setSelectedCompanyName("")
                    setSelectedCompany("")
                  }
                }}
                onCompanySelect={handleCompanySelectFromDropdown}
                onCreateNew={handleCreateNewCompany}
              />
            </div>

            {/* Global time range filter */}
            <div className="ds-topbar-actions">
              {error && (
                <span style={{ fontSize: 12, color: "var(--rose-700)", maxWidth: 240 }} className="truncate">
                  {error}
                </span>
              )}
              <div className="ds-time-filter">
                {[
                  { value: "all", label: "Standard" },
                  { value: "1y",  label: "1 Jahr" },
                  { value: "3y",  label: "3 Jahre" },
                ].map(({ value, label }) => (
                  <button
                    key={value}
                    className={`ds-time-btn${globalTimeRange === value ? " active" : ""}`}
                    onClick={() => setGlobalTimeRange(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* CONTENT */}
          <div className="ds-content">

            {/* Page heading */}
            {selectedCompanyName && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                  <h1 style={{ margin: 0, font: "600 24px/30px var(--font-sans)", letterSpacing: "-0.015em", color: "var(--color-fg)" }}>
                    {selectedCompanyName}
                  </h1>
                  {(() => {
                    const cid = effectiveCompanyId
                    const co = companies.find(c => String(c.id) === String(cid))
                    return co?.review_count != null ? (
                      <span style={{ font: "400 13px/1 var(--font-sans)", color: "var(--color-fg-muted)" }}>
                        {co.review_count} Bewertungen
                      </span>
                    ) : null
                  })()}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 4, flexWrap: "wrap" }}>
                  <p style={{ margin: 0, font: "400 13px/1.5 var(--font-sans)", color: "var(--color-fg-muted)" }}>
                    Übersicht aller Bewertungen, Topics und Trends.
                  </p>
                  {importHistory.length > 0 && (
                    <span
                      style={{
                        display: "inline-flex", alignItems: "center", gap: 4,
                        font: "400 11px/1 var(--font-sans)", color: "var(--color-fg-subtle)",
                        padding: "3px 8px", borderRadius: "var(--radius-full)",
                        border: "1px solid var(--color-border)", background: "var(--slate-50)",
                      }}
                      title={`Import-Verlauf: ${importHistory.length} Einträge`}
                    >
                      <Clock style={{ width: 10, height: 10 }} />
                      Letzter Import:{" "}
                      {new Date(importHistory[0].timestamp).toLocaleString("de-DE", {
                        day: "2-digit", month: "2-digit", year: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Error banner */}
            {error && <div className="ds-error">{error}</div>}

            {/* KPI section heading */}
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
              <h2 style={{ margin: 0, font: "600 14px/20px var(--font-sans)", color: "var(--color-fg)" }}>Kennzahlen</h2>
              <span style={{ font: "400 12px/1 var(--font-sans)", color: "var(--color-fg-subtle)" }}>
                Karte anklicken öffnet Detailansicht
              </span>
            </div>

            {/* KPI Grid (expandable cards) */}
            <div style={{ marginBottom: 20 }}>
              <KPIGrid
                companyId={effectiveCompanyId}
                avgScore={data?.avg_overall}
                avgCount={null}
                trendData={trendData}
                mostCriticalData={mostCriticalData}
                negativeTopicItem={negativeTopicItem}
                getNegativeTopicName={getNegativeTopicName}
                onOpenScore={() => setOpen(true)}
                onOpenTrend={() => setOpenTrend(true)}
                onOpenCritical={() => setOpenMostCritical(true)}
                onOpenNegative={() => setOpenNegative(true)}
                topicOverviewRef={topicOverviewRef}
              />
            </div>

            {/* Charts row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <TimelineCard
                companyId={selectedCompany || selectedCompanyId}
                onFiltersChange={handleTimelineFiltersChange}
                onLoadingChange={handleTimelineLoadingChange}
                globalTimeRange={globalTimeRange}
              />
              <TopicRatingCard
                companyId={selectedCompany || selectedCompanyId}
                onFiltersChange={handleTopicRatingFiltersChange}
                onLoadingChange={handleTopicRatingLoadingChange}
                globalTimeRange={globalTimeRange}
              />
            </div>

            {/* Topic overview */}
            <TopicOverviewCard
              ref={topicOverviewRef}
              companyId={selectedCompany || selectedCompanyId}
              onDataChange={handleTopicOverviewDataChange}
              onLoadingChange={handleTopicOverviewLoadingChange}
              globalTimeRange={globalTimeRange}
            />

          </div>
        </div>
      </div>

      {/* ---- Modals ---- */}
      <SorceModal
        open={open}
        onOpenChange={setOpen}
        companyId={selectedCompany}
      />

      <TrendModal
        open={openTrend}
        onOpenChange={setOpenTrend}
        companyId={effectiveCompanyId}
      />

      <MostCriticalModal
        open={openMostCritical}
        onOpenChange={setOpenMostCritical}
        companyId={effectiveCompanyId}
      />

      <NegativTopicModal
        open={openNegative}
        onOpenChange={setOpenNegative}
        companyId={effectiveCompanyId}
        topic={negativeTopicItem}
      />

      <ImportModal
        open={openImport}
        onOpenChange={setOpenImport}
        companyId={effectiveCompanyId}
        companyName={selectedCompanyName}
        onImportSuccess={handleImportSuccess}
      />
    </>
  )
}
