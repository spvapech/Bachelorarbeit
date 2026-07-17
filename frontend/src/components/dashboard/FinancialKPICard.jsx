import * as React from "react"
import { useState, useEffect, useCallback, memo } from "react"
import { Landmark, RefreshCw, Users, PieChart, Wallet, Building2 } from "lucide-react"
import { API_URL } from "@/config"
import { ChartCardHeader } from "./ChartHeader"
import { KPITile } from "./KPIGrid"

const CURRENCY_SYMBOL = { EUR: "€", USD: "$", GBP: "£" }

function formatMoney(value, currency) {
    const n = Number(value)
    if (!Number.isFinite(n) || n === 0) return "—"
    const symbol = CURRENCY_SYMBOL[currency] || currency || ""
    const fmt = (v) => v.toFixed(1).replace(".", ",")
    if (Math.abs(n) >= 1e9) return `${fmt(n / 1e9)} Mrd. ${symbol}`.trim()
    if (Math.abs(n) >= 1e6) return `${fmt(n / 1e6)} Mio. ${symbol}`.trim()
    return `${n.toLocaleString("de-DE")} ${symbol}`.trim()
}

function formatNumber(value, digits = 1) {
    const n = Number(value)
    if (!Number.isFinite(n) || n === 0) return "—"
    return n.toFixed(digits).replace(".", ",")
}

/* ============================================================================
   FinancialKPICard — zentrale Unternehmenskennzahlen (Yahoo Finance,
   persistiert): Marktkapitalisierung, KGV, Umsatz, Mitarbeiter.
   ============================================================================ */
export const FinancialKPICard = memo(function FinancialKPICard({ companyId }) {
    const [kpis, setKpis] = useState(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [error, setError] = useState(null)

    const fetchKpis = useCallback(async () => {
        if (!companyId) return
        try {
            setError(null)
            const res = await fetch(`${API_URL}/context/company/${companyId}/kpis`)
            if (res.status === 404) { setKpis(null); return }
            if (!res.ok) throw new Error(`API Error (kpis): ${res.status}`)
            setKpis(await res.json())
        } catch (e) {
            console.error("Error fetching financial KPIs:", e)
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }, [companyId])

    useEffect(() => {
        if (!companyId) { setLoading(false); setKpis(null); return }
        setLoading(true)
        fetchKpis()
    }, [companyId, fetchKpis])

    const refresh = async (e) => {
        e?.stopPropagation()
        if (!companyId) return
        setRefreshing(true)
        try {
            await fetch(`${API_URL}/context/company/${companyId}/refresh?sources=kpis`, { method: "POST" })
            await fetchKpis()
        } catch (err) {
            console.error("Error refreshing KPIs:", err)
        } finally {
            setRefreshing(false)
        }
    }

    const currency = kpis?.currency
    const fetchedAt = kpis?.fetched_at
        ? new Date(kpis.fetched_at).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
        : null

    const emptyMessage =
        !companyId ? "Keine Firma ausgewählt"
        : error ? `Fehler: ${error}`
        : !kpis ? "Keine Kennzahlen persistiert — Ticker einrichten und Daten laden (Aktienkurs-Karte)"
        : null

    return (
        <div className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow flex flex-col h-full">
            <ChartCardHeader
                icon={<Landmark />}
                eyebrow="FINANZMARKT · KENNZAHLEN"
                title="Unternehmenskennzahlen"
                subtitle={kpis?.ticker ? `${kpis.ticker} · Yahoo Finance` : "Einordnung im Dashboard"}
                actions={kpis ? (
                    <button
                        title="Kennzahlen neu laden (Yahoo Finance)"
                        onClick={refresh}
                        className="h-7 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-white text-slate-600 border border-slate-300 hover:bg-slate-50 transition-colors"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                        Aktualisieren
                    </button>
                ) : null}
            />

            <div className="px-4 pt-4 pb-4 flex flex-col flex-1 min-h-0 relative">
                {emptyMessage ? (
                    <div className="flex-1 flex items-center justify-center min-h-[180px]">
                        <p className="text-[13px] text-slate-500 text-center max-w-[280px]">{emptyMessage}</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <KPITile
                            label="Marktkapitalisierung"
                            icon={<Building2 />}
                            tone="neutral"
                            value={formatMoney(kpis.market_cap, currency)}
                            valueSize="sm"
                            footer="Börsenwert"
                            disabled
                        />
                        <KPITile
                            label="KGV (trailing)"
                            icon={<PieChart />}
                            tone="neutral"
                            value={formatNumber(kpis.trailing_pe)}
                            valueSize="sm"
                            footer="Kurs-Gewinn-Verhältnis"
                            disabled
                        />
                        <KPITile
                            label="Umsatz"
                            icon={<Wallet />}
                            tone="neutral"
                            value={formatMoney(kpis.revenue, currency)}
                            valueSize="sm"
                            footer="letzte 12 Monate"
                            disabled
                        />
                        <KPITile
                            label="Mitarbeiter"
                            icon={<Users />}
                            tone="neutral"
                            value={kpis.employees ? Number(kpis.employees).toLocaleString("de-DE") : "—"}
                            valueSize="sm"
                            footer="Vollzeitäquivalente"
                            disabled
                        />
                    </div>
                )}

                {(loading || refreshing) && (
                    <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
                        <div className="flex items-center gap-2">
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                            <p className="text-slate-600 text-[12px]">Lade Kennzahlen…</p>
                        </div>
                    </div>
                )}

                <div className="flex-1" />
                {fetchedAt && (
                    <p className="text-[11px] text-slate-400 text-center mt-3 m-0">
                        Stand: {fetchedAt} · Yahoo Finance (persistiert)
                    </p>
                )}
            </div>
        </div>
    )
})
