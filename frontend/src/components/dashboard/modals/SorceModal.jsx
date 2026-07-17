import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { ArrowDown, ArrowUp, Filter, Search, Star as StarIcon, X } from "lucide-react";
import ModalShell, { ModalLoader, ModalError } from "./ModalShell";
import { Star } from "../../../icons";

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
  avg_interessante_aufgaben: "Interessante Aufgaben",
  avg_umgang_aelteren_kollegen: "Umgang mit älteren Kollegen",
  avg_arbeitsbedingungen: "Arbeitsbedingungen",
  avg_gleichberechtigung: "Gleichberechtigung",
  avg_kommunikation: "Kommunikation",
};

/* Tone for a single score */
const scoreTone = (s) => {
  const n = Number(s);
  if (!Number.isFinite(n)) return { bg: "bg-slate-100", text: "text-slate-600", bar: "bg-slate-300" };
  if (n >= 3.5) return { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-500" };
  if (n >= 2.5) return { bg: "bg-amber-50",   text: "text-amber-700",   bar: "bg-amber-500" };
  return            { bg: "bg-rose-50",    text: "text-rose-700",    bar: "bg-rose-500" };
};

function ScoreStars({ score }) {
  const filled = Math.max(0, Math.min(5, Math.round(score)));
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <StarIcon
          key={i}
          className={["h-3.5 w-3.5", i < filled ? "fill-amber-400 text-amber-400" : "text-slate-300"].join(" ")}
        />
      ))}
    </div>
  );
}

export default function SorceModal({ open, onOpenChange, companyId }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  const [searchTerm, setSearchTerm]   = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [minScore, setMinScore]       = useState("");
  const [maxScore, setMaxScore]       = useState("");
  const [sortKey, setSortKey]         = useState("score");
  const [sortDir, setSortDir]         = useState("asc");

  useEffect(() => {
    if (!open) return;
    setLoading(true); setError("");
    fetch(`${API_URL}/companies/${companyId}/ratings/avg`)
      .then((r) => { if (!r.ok) throw new Error("API error"); return r.json(); })
      .then(setData)
      .catch((e) => setError(e.message || "Error"))
      .finally(() => setLoading(false));
  }, [open, companyId]);

  const rows = useMemo(() => {
    if (!data) return [];
    return Object.entries(data)
      .map(([key, value]) => ({ key, title: LABELS[key] ?? key, score: Number(value) }))
      .filter((x) => Number.isFinite(x.score));
  }, [data]);

  const filteredRows = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    const min = minScore === "" ? null : Number(minScore);
    const max = maxScore === "" ? null : Number(maxScore);
    let list = rows;
    if (q) list = list.filter((r) => r.title.toLowerCase().includes(q));
    if (min !== null && Number.isFinite(min)) list = list.filter((r) => r.score >= min);
    if (max !== null && Number.isFinite(max)) list = list.filter((r) => r.score <= max);
    const dir = sortDir === "desc" ? -1 : 1;
    return [...list].sort((a, b) =>
      sortKey === "title" ? a.title.localeCompare(b.title) * dir : (a.score - b.score) * dir
    );
  }, [rows, searchTerm, minScore, maxScore, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  };

  const resetFilters = () => {
    setSearchTerm(""); setMinScore(""); setMaxScore(""); setSortKey("score"); setSortDir("asc");
  };

  // Overall avg for header subtitle
  const overall = rows.length ? rows.reduce((s, r) => s + r.score, 0) / rows.length : null;
  const overallTone = overall ? scoreTone(overall) : null;

  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      tone={overall ? (overall >= 3.5 ? "good" : overall >= 2.5 ? "warn" : "bad") : "neutral"}
      icon={<Star />}
      eyebrow="KENNZAHL · BEWERTUNGS­ÜBERSICHT"
      title="Ø Score · Kategorien"
      subtitle={
        overall
          ? `Durchschnitt über alle Kategorien: ${overall.toFixed(2).replace(".", ",")} / 5`
          : "Detaillierte Bewertung pro Kategorie"
      }
      size="lg"
      toolbar={
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Kategorie filtern…"
                className="h-8 pl-8 text-[13px]"
              />
            </div>
            <button
              onClick={() => setFiltersOpen((v) => !v)}
              className={[
                "h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium border transition-colors",
                filtersOpen
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50",
              ].join(" ")}
            >
              <Filter className="h-3.5 w-3.5" /> Filter
            </button>
            <button
              onClick={resetFilters}
              className="h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
            >
              <X className="h-3.5 w-3.5" /> Reset
            </button>
          </div>

          {filtersOpen && (
            <div className="flex flex-wrap items-end gap-3 p-2.5 rounded-md border border-slate-200 bg-white">
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">Min</label>
                <Input type="number" step="0.1" min="0" max="5"
                  value={minScore} onChange={(e) => setMinScore(e.target.value)}
                  className="h-8 w-20 text-[13px]" />
              </div>
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">Max</label>
                <Input type="number" step="0.1" min="0" max="5"
                  value={maxScore} onChange={(e) => setMaxScore(e.target.value)}
                  className="h-8 w-20 text-[13px]" />
              </div>
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">Sortieren</label>
                <div className="flex gap-1.5">
                  <button onClick={() => toggleSort("score")} className={[
                    "h-8 px-2.5 inline-flex items-center gap-1 rounded-md text-[12px] font-medium border",
                    sortKey === "score" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"
                  ].join(" ")}>
                    Score {sortKey === "score" && (sortDir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                  </button>
                  <button onClick={() => toggleSort("title")} className={[
                    "h-8 px-2.5 inline-flex items-center gap-1 rounded-md text-[12px] font-medium border",
                    sortKey === "title" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"
                  ].join(" ")}>
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

      {!loading && !error && (
        <div className="flex flex-col">
          {filteredRows.map((row, idx) => {
            const t = scoreTone(row.score);
            return (
              <div
                key={row.key}
                className={[
                  "grid items-center gap-3 py-2.5",
                  idx < filteredRows.length - 1 ? "border-b border-slate-100" : "",
                ].join(" ")}
                style={{ gridTemplateColumns: "1.4fr 90px 1fr 56px" }}
              >
                <span className="font-medium text-[13px] text-slate-900 truncate" title={row.title}>
                  {row.title}
                </span>
                <ScoreStars score={row.score} />
                <span className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <span
                    className={["h-full rounded-full block", t.bar].join(" ")}
                    style={{ width: `${(row.score / 5) * 100}%`, transition: "width 400ms ease" }}
                  />
                </span>
                <span className={["text-right font-semibold tnum text-[13px]", t.text].join(" ")}>
                  {row.score.toFixed(2).replace(".", ",")}
                </span>
              </div>
            );
          })}

          {filteredRows.length === 0 && (
            <div className="py-8 text-center text-[13px] text-slate-500">
              Keine Treffer für diese Filter.
            </div>
          )}
        </div>
      )}
    </ModalShell>
  );
}
