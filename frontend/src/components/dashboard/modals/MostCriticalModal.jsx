import React, { useEffect, useMemo, useState } from "react";
import { TrendingDown, BarChart3, Layers } from "lucide-react";
import ModalShell, { ModalLoader, ModalError, ModalEmpty } from "./ModalShell";
import { Alert } from "../../../icons";
import { API_URL } from "../../../config";

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

const fmt = (n, d = 2) => Number(n).toFixed(d).replace(".", ",");

export default function MostCriticalModal({ open, onOpenChange, companyId = null }) {
  const [item, setItem]       = useState(null);
  const [allEntries, setAll]  = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => {
    if (!open) return;
    if (!companyId) { setItem(null); setError("Keine Firma ausgewählt"); return; }

    setLoading(true); setError(null);
    fetch(`${API_URL}/companies/${companyId}/ratings/avg`)
      .then((res) => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
      .then((data) => {
        if (!data || typeof data !== "object") { setItem(null); return; }
        const entries = Object.entries(data)
          .map(([k, v]) => ({ key: k, title: LABELS[k] ?? k, score: Number(v) }))
          .filter((x) => Number.isFinite(x.score));
        if (!entries.length) { setItem(null); return; }
        const sorted = [...entries].sort((a, b) => a.score - b.score);
        const min = sorted[0];
        const negative_share_percent = Math.max(0, Math.min(100, Math.round(((5 - min.score) / 5) * 100)));
        setItem({ ...min, negative_share_percent });
        setAll(sorted);
      })
      .catch((err) => { setError(err.message || "Fehler beim Laden"); setItem(null); })
      .finally(() => setLoading(false));
  }, [open, companyId]);

  const negP = useMemo(() => {
    if (!item) return null;
    const p = Number(item.negative_share_percent);
    return Number.isFinite(p) ? Math.round(p) : null;
  }, [item]);

  const impact = useMemo(() => {
    if (negP === null) return "-";
    if (negP >= 60) return "Hoch";
    if (negP >= 35) return "Mittel";
    return "Niedrig";
  }, [negP]);

  const impactTone = impact === "Hoch" ? "bad" : impact === "Mittel" ? "warn" : "good";
  const impactColor = {
    Hoch:    "bg-rose-50 text-rose-700 border-rose-200",
    Mittel:  "bg-amber-50 text-amber-700 border-amber-200",
    Niedrig: "bg-emerald-50 text-emerald-700 border-emerald-200",
  }[impact] ?? "bg-slate-50 text-slate-700 border-slate-200";

  const tone = item
    ? (item.score >= 3.5 ? "good" : item.score >= 2.5 ? "warn" : "bad")
    : "neutral";

  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      tone={tone}
      icon={<Alert />}
      eyebrow="KENNZAHL · KRITISCHSTES THEMA"
      title={loading || error || !item ? "Most Critical" : item.title}
      subtitle={item ? `Niedrigster Topic-Score: ${fmt(item.score)} / 5` : "Kategorie mit dem niedrigsten Score"}
      size="md"
    >
      {loading && <ModalLoader />}
      {error && <ModalError>Fehler: {error}</ModalError>}
      {!loading && !error && !item && <ModalEmpty>Keine kritischste Kategorie gefunden.</ModalEmpty>}

      {!loading && !error && item && (
        <div className="space-y-3">

          {/* Anteil negativer Reviews */}
          <div className="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-3.5 py-2.5">
            <div className="flex items-center gap-2 text-[13px] font-medium text-slate-700">
              <TrendingDown className="h-4 w-4 text-rose-500" />
              Anteil negativer Reviews
            </div>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-semibold bg-rose-50 text-rose-700 tnum">
              {negP === null ? "—" : `${negP} %`}
            </span>
          </div>

          {/* Impact-Indikator */}
          <div className="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-3.5 py-2.5">
            <div className="flex items-center gap-2 text-[13px] font-medium text-slate-700">
              <BarChart3 className="h-4 w-4 text-amber-500" />
              Impact-Indikator
            </div>
            <span className={["text-[12px] font-semibold px-2 py-0.5 rounded-full border", impactColor].join(" ")}>
              {impact}
            </span>
          </div>

          {/* Vergleich aller Kategorien */}
          {allEntries.length > 0 && (
            <div className="rounded-md border border-slate-200 bg-white">
              <div className="px-3.5 py-2 border-b border-slate-200 flex items-center gap-2 text-[13px] font-medium text-slate-700">
                <Layers className="h-4 w-4 text-slate-500" />
                Alle Kategorien (sortiert)
              </div>
              <div className="divide-y divide-slate-100">
                {allEntries.slice(0, 6).map((c) => {
                  const tone = c.score >= 3.5
                    ? { bar: "bg-emerald-500", text: "text-emerald-700" }
                    : c.score >= 2.5
                      ? { bar: "bg-amber-500", text: "text-amber-700" }
                      : { bar: "bg-rose-500", text: "text-rose-700" };
                  return (
                    <div
                      key={c.key}
                      className="grid items-center gap-3 px-3.5 py-2"
                      style={{ gridTemplateColumns: "1.6fr 1fr 56px" }}
                    >
                      <span className="text-[12.5px] text-slate-700 truncate" title={c.title}>
                        {c.title}
                      </span>
                      <span className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <span
                          className={["h-full rounded-full block", tone.bar].join(" ")}
                          style={{ width: `${(c.score / 5) * 100}%` }}
                        />
                      </span>
                      <span className={["text-right font-semibold tnum text-[12.5px]", tone.text].join(" ")}>
                        {fmt(c.score)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </ModalShell>
  );
}
