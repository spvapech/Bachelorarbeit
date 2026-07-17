import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { ArrowDown, ArrowUp, Filter, Search, TrendingDown, TrendingUp, Minus, X } from "lucide-react";
import ModalShell, { ModalLoader, ModalError, ModalEmpty } from "./ModalShell";
import { TrendUp as TrendUpIcon } from "../../../icons";

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";

const LABELS = {
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
  avg_umgang_aelteren_kollegen: "Umgang mit älteren Kollegen",
  avg_arbeitsbedingungen: "Arbeitsbedingungen",
  avg_gleichberechtigung: "Gleichberechtigung",
};

const RANGE_TO_STABLE_MONTHS = { "1Y": 12, "3Y": 36 };
const RANGE_TO_DAYS_FALLBACK = { "All": 730 };

const fmtDelta = (d, sign) => {
  if (sign === "new")    return "neu";
  if (sign === "nodata") return "k.A.";
  if (d === null || !Number.isFinite(d)) return "k.A.";
  const v = Math.round(d * 10) / 10;
  const a = Math.abs(v).toFixed(1).replace(".", ",");
  if (sign === "up")   return `+${a}`;
  if (sign === "down") return `−${a}`;
  return v.toFixed(1).replace(".", ",");
};

const signTone = (sign) => {
  if (sign === "up")     return { text: "text-emerald-700", bg: "bg-emerald-50", icon: TrendingUp };
  if (sign === "down")   return { text: "text-rose-700",    bg: "bg-rose-50",    icon: TrendingDown };
  if (sign === "new")    return { text: "text-blue-700",    bg: "bg-blue-50",    icon: Minus };
  if (sign === "nodata") return { text: "text-slate-400",   bg: "bg-slate-50",   icon: Minus };
  return { text: "text-slate-600", bg: "bg-slate-100", icon: Minus };
};

export default function TrendModal({ open, onOpenChange, companyId }) {
  const [range, setRange]     = useState("1Y");
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const [searchTerm, setSearchTerm]   = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [signFilter, setSignFilter]   = useState("all");
  const [sortKey, setSortKey]         = useState("delta");
  const [sortDir, setSortDir]         = useState("desc");

  useEffect(() => {
    if (!open || !companyId) return;
    const stableMonths = RANGE_TO_STABLE_MONTHS[range];
    const daysFallback = RANGE_TO_DAYS_FALLBACK[range];

    const controller = new AbortController();
    setLoading(true); setError("");

    const url = stableMonths
      ? `${API_URL}/companies/${companyId}/ratings/trend?mode=stable_months&months=${stableMonths}`
      : range === "All"
        ? `${API_URL}/companies/${companyId}/ratings/trend?mode=stable_all&months=12`
        : `${API_URL}/companies/${companyId}/ratings/trend?days=${daysFallback ?? 30}`;

    fetch(url, { signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error("API error"); return r.json(); })
      .then(setData)
      .catch((e) => { if (e.name !== "AbortError") setError(e.message || "Failed to fetch"); })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [open, companyId, range]);

  const rows = useMemo(() => {
    if (!data) return [];
    const metrics = data.metrics ?? data;
    return Object.entries(metrics)
      .map(([key, obj]) => {
        const delta = obj?.delta == null ? null : Number(obj.delta);
        // delta===null means no data in current window — don't show as flat 0,0
        const sign = delta === null && obj?.sign !== "new" ? "nodata" : (obj?.sign ?? "flat");
        return { key, title: LABELS[key] ?? key, delta, sign };
      })
      .filter((x) => Boolean(x.title));
  }, [data]);

  const filtered = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    let next = rows;
    if (q) next = next.filter((r) => r.title.toLowerCase().includes(q));
    if (signFilter !== "all") next = next.filter((r) => (r.sign ?? "flat") === signFilter);
    const dir = sortDir === "desc" ? -1 : 1;
    const safeDelta = (r) => r.sign === "new" ? Number.POSITIVE_INFINITY : (Number.isFinite(r.delta) ? r.delta : 0);
    return [...next].sort((a, b) =>
      sortKey === "title"
        ? dir * a.title.localeCompare(b.title, "de", { sensitivity: "base" })
        : dir * (safeDelta(a) - safeDelta(b))
    );
  }, [rows, searchTerm, signFilter, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir(key === "title" ? "asc" : "desc"); }
  };
  const clearFilters = () => { setSearchTerm(""); setSignFilter("all"); setSortKey("delta"); setSortDir("desc"); };

  // Derive overall trend tone for the modal header
  const overallTone = useMemo(() => {
    if (!rows.length) return "neutral";
    const ups = rows.filter((r) => r.sign === "up").length;
    const downs = rows.filter((r) => r.sign === "down").length;
    if (ups > downs * 1.2) return "good";
    if (downs > ups * 1.2) return "bad";
    return "neutral";
  }, [rows]);

  const SignChip = ({ sign }) => {
    const { Icon = Minus } = { Icon: signTone(sign).icon };
    const t = signTone(sign);
    return (
      <span className={["inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[12px] font-semibold", t.bg, t.text].join(" ")}>
        <Icon className="h-3 w-3" />
        <span className="tnum">{fmtDelta(rows.find(r=>r.sign===sign)?.delta, sign)}</span>
      </span>
    );
  };

  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      tone={overallTone}
      icon={<TrendUpIcon />}
      eyebrow="KENNZAHL · TREND-ENTWICKLUNG"
      title="Trend pro Kategorie"
      subtitle={`Vergleich · ${range === "All" ? "Gesamt" : range === "1Y" ? "Letzte 12 Monate" : "Letzte 36 Monate"}`}
      size="lg"
      toolbar={
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Kategorie filtern…"
                className="h-8 pl-8 text-[13px]"
              />
            </div>

            {/* Range picker */}
            <div className="inline-flex bg-white border border-slate-300 rounded-md p-0.5">
              {["1Y", "3Y", "All"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={[
                    "h-7 px-3 rounded-[4px] text-[12px] font-medium transition-colors",
                    range === r ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900",
                  ].join(" ")}
                >
                  {r}
                </button>
              ))}
            </div>

            <button
              onClick={() => setFiltersOpen((v) => !v)}
              className={[
                "h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium border",
                filtersOpen ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50",
              ].join(" ")}
            >
              <Filter className="h-3.5 w-3.5" /> Filter
            </button>
            <button
              onClick={clearFilters}
              className="h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
            >
              <X className="h-3.5 w-3.5" /> Reset
            </button>
          </div>

          {filtersOpen && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-2.5 rounded-md border border-slate-200 bg-white">
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1.5">Trend</label>
                <div className="flex flex-wrap gap-1">
                  {[
                    { k: "all",  label: "Alle" },
                    { k: "up",   label: "↑ Steigend" },
                    { k: "down", label: "↓ Sinkend" },
                    { k: "flat", label: "→ Stabil" },
                    { k: "new",  label: "Neu" },
                  ].map((opt) => (
                    <button
                      key={opt.k}
                      onClick={() => setSignFilter(opt.k)}
                      className={[
                        "h-7 px-2.5 rounded-md text-[12px] font-medium border",
                        signFilter === opt.k ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300",
                      ].join(" ")}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1.5">Sortierung</label>
                <div className="flex flex-wrap gap-1">
                  <button
                    onClick={() => toggleSort("delta")}
                    className={[
                      "h-7 px-2.5 rounded-md text-[12px] font-medium border inline-flex items-center gap-1",
                      sortKey === "delta" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300",
                    ].join(" ")}
                  >
                    Δ {sortKey === "delta" && (sortDir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                  </button>
                  <button
                    onClick={() => toggleSort("title")}
                    className={[
                      "h-7 px-2.5 rounded-md text-[12px] font-medium border inline-flex items-center gap-1",
                      sortKey === "title" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300",
                    ].join(" ")}
                  >
                    Kategorie {sortKey === "title" && (sortDir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      }
    >
      {loading && <ModalLoader />}
      {error && <ModalError>{error}</ModalError>}
      {!companyId && <ModalEmpty>Bitte zuerst eine Firma auswählen.</ModalEmpty>}

      {!loading && !error && companyId && (
        <div className="flex flex-col">
          {filtered.length === 0 && (
            <ModalEmpty>{rows.length === 0 ? "Keine Trend-Daten für diesen Zeitraum." : "Keine Treffer (Filter anpassen)."}</ModalEmpty>
          )}

          {filtered.map((row, idx) => {
            const t = signTone(row.sign);
            const Icon = t.icon;
            return (
              <div
                key={row.key}
                className={[
                  "flex items-center justify-between py-2.5 gap-3",
                  idx < filtered.length - 1 ? "border-b border-slate-100" : "",
                ].join(" ")}
              >
                <span className="text-[13px] font-medium text-slate-900 truncate flex-1">
                  {row.title}
                </span>
                <span className={["inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[12px] font-semibold tnum", t.bg, t.text].join(" ")}>
                  <Icon className="h-3.5 w-3.5" />
                  {fmtDelta(row.delta, row.sign)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </ModalShell>
  );
}
