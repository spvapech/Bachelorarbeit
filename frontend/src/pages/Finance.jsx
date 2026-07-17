import * as React from "react"
import { useState, useEffect, useMemo, useCallback } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { Newspaper, Megaphone, ExternalLink, FileText } from "lucide-react"

import { WorkPulseLogo } from "@/components/WorkPulseLogo"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { StockChartCard } from "@/components/dashboard/StockChartCard"
import { FinancialKPICard } from "@/components/dashboard/FinancialKPICard"
import { AnalystRecommendationsCard } from "@/components/dashboard/AnalystRecommendationsCard"
import { ChartCardHeader } from "@/components/dashboard/ChartHeader"

import {
  Dashboard as DashboardIcon, Compare, Building, Home, Search, Sun, Moon, TrendUp,
} from "../icons"
import { useTheme } from "../hooks/useTheme"
import { API_URL } from "../config"

/* Quelltyp → Badge (konsistent mit AnomalyExplanationsCard) */
const SOURCE_BADGES = {
  news: { label: "News", cls: "bg-blue-50 text-blue-700 border-blue-200", icon: Newspaper },
  adhoc: { label: "Ad-hoc", cls: "bg-amber-50 text-amber-700 border-amber-200", icon: Megaphone },
}

function SourceBadge({ sourceType }) {
  const badge = SOURCE_BADGES[sourceType] || { label: "Manuell", cls: "bg-slate-100 text-slate-600 border-slate-200", icon: FileText }
  const Icon = badge.icon
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-medium flex-none ${badge.cls}`}>
      <Icon className="w-3 h-3" />
      {badge.label}
    </span>
  )
}

/* ============================================================================
   NewsListCard — persistierte Unternehmensnachrichten & Ad-hoc-Mitteilungen
   ============================================================================ */
function NewsListCard({ companyId, globalTimeRange }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!companyId) { setLoading(false); setItems([]); return }
    let cancelled = false
    const fetchNews = async () => {
      setLoading(true)
      try {
        setError(null)
        const res = await fetch(`${API_URL}/context/company/${companyId}/news`)
        if (!res.ok) throw new Error(`API Error (news): ${res.status}`)
        const json = await res.json()
        if (!cancelled) setItems(json.items || [])
      } catch (e) {
        console.error("Error fetching news:", e)
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchNews()
    return () => { cancelled = true }
  }, [companyId])

  const filtered = useMemo(() => {
    let list = [...items]
    if (globalTimeRange !== "all") {
      const years = globalTimeRange === "1y" ? 1 : 3
      const cutoff = new Date()
      cutoff.setFullYear(cutoff.getFullYear() - years)
      list = list.filter((i) => i.published_at && new Date(i.published_at) >= cutoff)
    }
    return list.sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || "")))
  }, [items, globalTimeRange])

  return (
    <div className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow flex flex-col">
      <ChartCardHeader
        icon={<Newspaper />}
        eyebrow="KONTEXTSAMMLUNG · EXTERNE QUELLEN"
        title="Nachrichten & Ad-hoc-Mitteilungen"
        subtitle={`${filtered.length} persistierte Ereignisse${globalTimeRange !== "all" ? " im gewählten Zeitraum" : ""}`}
      />
      <div className="relative min-h-[160px] max-h-[420px] overflow-y-auto">
        {loading ? (
          <div className="h-[160px] flex items-center justify-center">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
              <p className="text-slate-600 text-[12px] m-0">Lade Ereignisse…</p>
            </div>
          </div>
        ) : !companyId ? (
          <div className="h-[160px] flex items-center justify-center">
            <p className="text-[13px] text-slate-500 m-0">Keine Firma ausgewählt</p>
          </div>
        ) : error ? (
          <div className="h-[160px] flex items-center justify-center">
            <p className="text-[13px] text-slate-500 m-0">Fehler: {error}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="h-[160px] flex items-center justify-center px-6 text-center">
            <p className="text-[13px] text-slate-500 m-0">
              Keine Ereignisse persistiert — über die Aktienkurs-Karte „Daten laden“ ausführen
              oder Ereignisse manuell importieren.
            </p>
          </div>
        ) : (
          <ul className="m-0 p-0 list-none divide-y divide-slate-100">
            {filtered.map((item) => (
              <li key={item.id} className="px-4 py-2.5 hover:bg-slate-50 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2 min-w-0">
                    <SourceBadge sourceType={item.source_type} />
                    <div className="min-w-0">
                      <p className="m-0 text-[13px] leading-5 font-medium text-slate-900 truncate">
                        {item.url ? (
                          <a href={item.url} target="_blank" rel="noreferrer"
                             className="hover:text-blue-700 inline-flex items-center gap-1">
                            {item.titel}
                            <ExternalLink className="w-3 h-3 text-slate-400 flex-none" />
                          </a>
                        ) : item.titel}
                      </p>
                      {item.zusammenfassung && (
                        <p className="m-0 mt-0.5 text-[11px] leading-4 text-slate-500 line-clamp-2">
                          {item.zusammenfassung}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 tnum flex-none">
                    {item.published_at
                      ? new Date(item.published_at).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
                      : "—"}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="text-[11px] text-slate-400 text-center py-2.5 border-t border-slate-100 m-0">
        Quellen: Yahoo Finance · EQS-News-RSS · manueller Import — persistiert, kein Live-Abruf
      </p>
    </div>
  )
}

/* ============================================================================
   Finance — eigenständige Finanzmarkt-Analyse (analog Dashboard/Vergleich):
   Aktienkursverlauf, Unternehmenskennzahlen, Nachrichten & Ad-hoc.
   ============================================================================ */
export default function Finance() {
  const location = useLocation()
  const navigate = useNavigate()
  const companyFromState = location.state?.companyId
  const companyNameFromState = location.state?.companyName

  const [companyQuery, setCompanyQuery] = useState(companyNameFromState || "")
  const [selectedCompanyId, setSelectedCompanyId] = useState(companyFromState || null)
  const [selectedCompanyName, setSelectedCompanyName] = useState(companyNameFromState || "")
  const [companies, setCompanies] = useState([])
  const [globalTimeRange, setGlobalTimeRange] = useState("all")
  const [contextInfo, setContextInfo] = useState(null)

  const { isDark, toggle: toggleTheme } = useTheme()

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const res = await fetch(`${API_URL}/companies`)
        if (!res.ok) return
        const d = await res.json()
        setCompanies(Array.isArray(d) ? d : [])
      } catch { /* Firmen-Liste ist optional */ }
    }
    fetchCompanies()
  }, [])

  // Ticker/ISIN für die Kopfzeile
  useEffect(() => {
    if (!selectedCompanyId) { setContextInfo(null); return }
    let cancelled = false
    const fetchInfo = async () => {
      try {
        const res = await fetch(`${API_URL}/context/company/${selectedCompanyId}`)
        if (res.ok && !cancelled) setContextInfo(await res.json())
      } catch { /* Kopfzeilen-Info ist optional */ }
    }
    fetchInfo()
    return () => { cancelled = true }
  }, [selectedCompanyId])

  const handleCompanySelect = useCallback((company) => {
    if (company) {
      setSelectedCompanyId(company.id)
      setSelectedCompanyName(company.name)
      setCompanyQuery(company.name)
    } else {
      setSelectedCompanyId(null)
      setSelectedCompanyName("")
    }
  }, [])

  const navState = selectedCompanyId
    ? { companyId: selectedCompanyId, companyName: selectedCompanyName }
    : {}

  return (
    <div className="ds-app">

      {/* ---- RAIL ---- */}
      <aside className="ds-rail">
        <div className="ds-brand">
          <WorkPulseLogo variant="badge" />
        </div>

        <div className="ds-nav-group">
          <span className="ds-nav-group-label">Analyse</span>
          <button className="ds-nav-link" onClick={() => navigate("/dashboard", { state: navState })}>
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
          <button className="ds-nav-link active">
            <TrendUp />
            Finanzmarkt
          </button>
        </div>

        <div className="ds-nav-group">
          <span className="ds-nav-group-label">Daten</span>
          <button className="ds-nav-link" onClick={() => navigate("/welcome")}>
            <Building />
            Firmen
            {companies.length > 0 && (
              <span className="ds-nav-count">{companies.length}</span>
            )}
          </button>
        </div>

        <div className="ds-nav-group" style={{ marginTop: "auto" }}>
          <span className="ds-nav-group-label">Aktionen</span>
          <button className="ds-nav-link" onClick={() => navigate("/welcome")}>
            <Home />
            Startseite
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
          <div className="ds-crumbs">
            <span>Finanzmarkt</span>
            {selectedCompanyName && (
              <>
                <span className="sep">/</span>
                <span className="cur">{selectedCompanyName}</span>
              </>
            )}
          </div>

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
                }
              }}
              onCompanySelect={handleCompanySelect}
              onCreateNew={() => navigate("/welcome")}
            />
          </div>

          <div className="ds-topbar-actions">
            <div className="ds-time-filter">
              {[
                { value: "all", label: "Standard" },
                { value: "1y", label: "1 Jahr" },
                { value: "3y", label: "3 Jahre" },
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

          {selectedCompanyName ? (
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                <h1 style={{ margin: 0, font: "600 24px/30px var(--font-sans)", letterSpacing: "-0.015em", color: "var(--color-fg)" }}>
                  {selectedCompanyName}
                </h1>
                {contextInfo?.ticker && (
                  <span style={{ font: "500 13px/1 var(--font-mono, monospace)", color: "var(--color-fg-muted)" }}>
                    {contextInfo.ticker}{contextInfo.isin ? ` · ${contextInfo.isin}` : ""}
                  </span>
                )}
              </div>
              <p style={{ margin: "4px 0 0", font: "400 13px/1.5 var(--font-sans)", color: "var(--color-fg-muted)" }}>
                Aktienkurs, Kennzahlen und externe Ereignisse zur Einordnung der Bewertungsverläufe.
              </p>
            </div>
          ) : (
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ margin: 0, font: "600 24px/30px var(--font-sans)", letterSpacing: "-0.015em", color: "var(--color-fg)" }}>
                Finanzmarkt-Analyse
              </h1>
              <p style={{ margin: "4px 0 0", font: "400 13px/1.5 var(--font-sans)", color: "var(--color-fg-muted)" }}>
                Firma auswählen, um Kursverlauf, Kennzahlen und Nachrichten zu sehen.
              </p>
            </div>
          )}

          {/* Kurs + Kennzahlen */}
          <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 16, marginBottom: 16 }}>
            <StockChartCard
              companyId={selectedCompanyId}
              globalTimeRange={globalTimeRange}
            />
            <FinancialKPICard companyId={selectedCompanyId} />
          </div>

          {/* Analystenempfehlungen + Nachrichten */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 3fr", gap: 16 }}>
            <AnalystRecommendationsCard companyId={selectedCompanyId} />
            <NewsListCard companyId={selectedCompanyId} globalTimeRange={globalTimeRange} />
          </div>

        </div>
      </div>
    </div>
  )
}
