import * as React from "react"
import { useState, useEffect, useMemo, memo, forwardRef, useImperativeHandle } from "react"
import { AlertTriangle, ArrowRight } from "lucide-react"
import { ChartCardHeader, SourceToggle } from "./ChartHeader"
import { Tag } from "../../icons"
import TopicDetailModal from "./modals/TopicDetailModal"
import TopicTableModal from "./modals/TopicTableModal"
import { API_URL } from "@/config"

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

const fmt = (n, d = 1) => Number.isFinite(Number(n)) ? Number(n).toFixed(d).replace(".", ",") : "—"

// Tonale Klassen (gleich wie in den anderen Karten)
const scoreColorClass = (s) =>
  !Number.isFinite(s)        ? "text-slate-700"
  : s >= 3.5                  ? "text-emerald-700"
  : s >= 2.5                  ? "text-amber-700"
                              : "text-rose-700"

const scoreBoxClass = (s) =>
  !Number.isFinite(s)        ? "bg-slate-50 border-slate-200"
  : s >= 3.5                  ? "bg-emerald-50 border-emerald-200"
  : s >= 2.5                  ? "bg-amber-50 border-amber-200"
                              : "bg-rose-50 border-rose-200"

export const TopicOverviewCard = memo(forwardRef(function TopicOverviewCard(
  { companyId = 1, onDataChange, onLoadingChange, globalTimeRange = "all" },
  ref
) {
  const [topicsData,       setTopicsData]       = useState([])
  const [totalReviews,     setTotalReviews]     = useState(null)
  const [loading,          setLoading]          = useState(true)
  const [refreshing,       setRefreshing]       = useState(false)
  const [error,            setError]            = useState(null)
  const [selectedTopic,    setSelectedTopic]    = useState(null)
  const [detailModalOpen,  setDetailModalOpen]  = useState(false)
  const [tableModalOpen,   setTableModalOpen]   = useState(false)
  const [sourceFilter,     setSourceFilter]     = useState("all")
  const [isModalOpen,      setIsModalOpen]      = useState(false)

  // Loading-State nach außen kommunizieren
  useEffect(() => {
    if (onLoadingChange) onLoadingChange(loading)
  }, [loading, onLoadingChange])

  // Daten laden
  useEffect(() => {
    if (!companyId) return

    const fetchTopics = async () => {
      const isFirst = topicsData.length === 0
      isFirst ? setLoading(true) : setRefreshing(true)
      try {
        setError(null)
        let url = `${API_URL}/analytics/company/${companyId}/topic-overview`
        const params = new URLSearchParams()
        if (sourceFilter && sourceFilter !== "all") params.set("source", sourceFilter)
        if (globalTimeRange !== "all") {
          const now = new Date()
          const years = globalTimeRange === "1y" ? 1 : 3
          const startDate = new Date(now.getFullYear() - years, now.getMonth(), now.getDate())
          params.set("start_date", startDate.toISOString().slice(0, 10))
        }
        const qs = params.toString()
        if (qs) url += `?${qs}`
        const res = await fetch(url)
        if (!res.ok) throw new Error(`API Error: ${res.status}`)
        const data = await res.json()
        setTopicsData(data.topics || [])
        setTotalReviews(data.total_reviews ?? null)
      } catch (err) {
        console.error("Error fetching topics:", err)
        setError(err.message)
        setTopicsData([])
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    }

    fetchTopics()
  }, [companyId, sourceFilter, globalTimeRange])

  // Stats
  const stats = useMemo(() => {
    const total = topicsData.length
    if (!total) return null
    const avg = topicsData.reduce((s, t) => s + (Number(t.avgRating) || 0), 0) / total
    const mentions = topicsData.reduce((s, t) => s + (Number(t.frequency) || 0), 0)
    const limited = topicsData.filter((t) => t.statistical_meta?.risk_level === "limited").length
    return { total, avg, mentions, limited }
  }, [topicsData])

  // Daten an Parent für PDF Export
  useEffect(() => {
    if (onDataChange && !loading) {
      onDataChange({
        topics: topicsData,
        sourceFilter: sourceFilter === "all" ? null : sourceFilter,
        stats: stats ? {
          totalTopics:   stats.total,
          avgRating:     stats.avg.toFixed(1),
          totalMentions: stats.mentions,
        } : { totalTopics: 0, avgRating: 0, totalMentions: 0 }
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicsData, sourceFilter, loading])

  useEffect(() => { setIsModalOpen(tableModalOpen || detailModalOpen) }, [tableModalOpen, detailModalOpen])

  useImperativeHandle(ref, () => ({
    openTopicByName: (name) => {
      const found = topicsData.find((t) => t.topic?.toLowerCase() === name?.toLowerCase())
      if (found) {
        setSelectedTopic(found)
        setDetailModalOpen(true)
      } else {
        setTableModalOpen(true)
      }
    }
  }), [topicsData])

  const handleCardClick = () => { if (!tableModalOpen && !detailModalOpen) setTableModalOpen(true) }
  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic)
    setTableModalOpen(false)
    setDetailModalOpen(true)
  }
  const handleBackToTable = () => {
    setDetailModalOpen(false)
    setTableModalOpen(true)
  }

  const reloadTopicWithSource = async (topicName, newSourceFilter) => {
    try {
      let url = `${API_URL}/analytics/company/${companyId}/topic-overview`
      if (newSourceFilter && newSourceFilter !== "all") url += `?source=${newSourceFilter}`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`API Error: ${res.status}`)
      const data = await res.json()
      const updated = (data.topics || []).find((t) => t.topic === topicName)
      if (updated) setSelectedTopic(updated)
    } catch (err) { console.error("Error reloading topic:", err) }
  }

  const handleDetailSourceFilterChange = async (newFilter) => {
    if (!selectedTopic) return
    const topicName = selectedTopic.topic
    setSourceFilter(newFilter || "all")
    await reloadTopicWithSource(topicName, newFilter)
  }

  // Empty / Error message für den Body
  const emptyMessage =
    !companyId          ? "Keine Firma ausgewählt"
    : error             ? `Fehler: ${error}`
    : !topicsData.length && !loading ? "Keine Topics gefunden"
    : null

  const showOverlay = loading || refreshing
  const overlayLabel = loading ? "Lade Topic-Daten…" : "Daten werden aktualisiert…"

  return (
    <>
      <div
        className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer"
        onClick={handleCardClick}
      >
        <ChartCardHeader
          icon={<Tag />}
          eyebrow="TOPIC-ÜBERSICHT"
          title="Themenbereiche"
          subtitle={`${SOURCE_LABEL[sourceFilter] ?? "Alle Quellen"}${stats ? ` · ${stats.total} Topics` : ""}`}
          expandable
          actions={
            <div onClick={(e) => e.stopPropagation()}>
              <SourceToggle
                value={sourceFilter}
                onChange={setSourceFilter}
                options={SOURCE_OPTIONS}
              />
            </div>
          }
        />

        <div className="px-4 pt-4 pb-4 relative">
          {/* Empty / Loading-Anzeige */}
          {emptyMessage && !showOverlay ? (
            <div className="py-12 flex items-center justify-center">
              <p className="text-[13px] text-slate-500">{emptyMessage}</p>
            </div>
          ) : (
            <>
              {/* Statistical Warning Banner */}
              {stats?.limited > 0 && (
                <div className="mb-4 px-3 py-2 rounded-md bg-rose-50 border border-rose-200 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold text-rose-800 leading-tight">
                      Begrenzte Datenbasis bei {stats.limited} Topic{stats.limited !== 1 ? "s" : ""}
                    </p>
                    <p className="text-[11px] text-rose-700 mt-0.5 leading-tight">
                      Weniger als 30 Reviews — Ergebnisse mit Vorsicht interpretieren
                    </p>
                  </div>
                </div>
              )}

              {/* Stats-Grid — gleicher Stil wie TopicRating-Modal-Stats */}
              {stats && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center px-3 py-2.5 bg-slate-50 rounded-md border border-slate-200">
                    <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Topics</p>
                    <p className="text-[20px] font-semibold tnum text-slate-900">{stats.total}</p>
                  </div>
                  <div className={`text-center px-3 py-2.5 rounded-md border ${scoreBoxClass(stats.avg)}`}>
                    <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Ø Rating</p>
                    <p className={`text-[20px] font-semibold tnum ${scoreColorClass(stats.avg)}`}>
                      {fmt(stats.avg, 2)}
                    </p>
                    {totalReviews != null && (
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {Number(totalReviews).toLocaleString("de-DE")} Bew.
                      </p>
                    )}
                  </div>
                  <div className="text-center px-3 py-2.5 bg-slate-50 rounded-md border border-slate-200">
                    <p className="font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-1">Erwähnungen</p>
                    <p className="text-[20px] font-semibold tnum text-slate-900">
                      {Number(stats.mentions).toLocaleString("de-DE")}
                    </p>
                  </div>
                </div>
              )}

              {/* CTA-Footer */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-500">
                  Karte anklicken zeigt alle Topics in einer Tabelle
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-700 group-hover:text-blue-800">
                  Alle Topics
                  <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </>
          )}

          {/* Refresh-Overlay */}
          {showOverlay && (
            <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                <p className="text-slate-600 text-[12px]">{overlayLabel}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Table Modal */}
      <TopicTableModal
        open={tableModalOpen}
        onOpenChange={setTableModalOpen}
        topics={topicsData}
        onTopicSelect={handleTopicSelect}
        sourceFilter={sourceFilter === "all" ? null : sourceFilter}
        onSourceFilterChange={(s) => setSourceFilter(s || "all")}
      />

      {/* Detail Modal */}
      {selectedTopic && (
        <TopicDetailModal
          open={detailModalOpen}
          onOpenChange={setDetailModalOpen}
          topic={selectedTopic}
          onBackToTable={handleBackToTable}
          sourceFilter={sourceFilter === "all" ? null : sourceFilter}
          onSourceFilterChange={handleDetailSourceFilterChange}
          companyId={companyId}
        />
      )}
    </>
  )
}))
