import React, { useEffect, useState } from "react";
import { TrendingDown, MessageCircle, Layers } from "lucide-react";
import ModalShell, { ModalLoader, ModalError, ModalEmpty } from "./ModalShell";
import { Tag } from "../../../icons";
import { API_URL } from "../../../config";

export default function NegativTopicModal({ open, onOpenChange, topic: propTopic = null, companyId = null }) {
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ---- helpers (kept from original implementation) ---- */
  const toArray = (v) => (Array.isArray(v) ? v : v ? [v] : []);

  const deriveKritikpunkte = (m) => {
    if (!m) return [];
    const fromKritikpunkte = Array.isArray(m.kritikpunkte) ? m.kritikpunkte : [];
    if (fromKritikpunkte.length) return fromKritikpunkte;
    const fromTypical = Array.isArray(m.typicalStatements) ? m.typicalStatements : [];
    if (fromTypical.length) return fromTypical;
    const fromReviewDetails = Array.isArray(m.reviewDetails)
      ? m.reviewDetails.map((d) => d?.preview).filter(Boolean) : [];
    if (fromReviewDetails.length) return fromReviewDetails;
    const fromExample = typeof m.example === "string" && m.example.trim() ? [m.example] : [];
    if (fromExample.length) return fromExample;
    const fromWords = toArray(m.topic_words).length
      ? toArray(m.topic_words)
      : (typeof m.topic_text === "string" ? m.topic_text.split(",").map((x) => x.trim()).filter(Boolean) : []);
    return fromWords;
  };

  const extractSubjectPhrase = (text) => {
    if (!text) return "";
    let t = String(text).replace(/\s+/g, " ").replace(/^[-••\s]+/, "").trim();
    if (t.includes("\n")) t = t.split("\n")[0].trim();
    t = t
      .replace(/^(leider|mittlerweile|eigentlich|grunds(ä|a)tzlich|insgesamt|generell)\s+/i, "")
      .replace(/^(es\s+gab|es\s+gibt|es\s+ist|man\s+hat|man\s+kann|ich\s+finde|ich\s+hatte|wir\s+haben)\s+/i, "");
    t = t.split(/[.!?;:()\[\]—–-]/)[0].trim();
    const stop = new Set([
      "und","oder","aber","dass","das","der","die","den","dem","des","ein","eine","einer","eines",
      "mit","ohne","für","auf","im","in","am","an","zu","von","bei","als","auch","nicht","nur",
      "ist","sind","war","waren","wird","werden","ich","wir","man","sehr","mehr","weniger","noch",
      "kein","keine","keinen","keiner","keines","über","unter","vor","nach","aus","um","wie","weil",
    ]);
    const words = t.split(/\s+/)
      .map((w) => w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, ""))
      .filter((w) => w.length >= 3 && !stop.has(w.toLowerCase()));
    const phrase = words.slice(0, 4).join(" ").trim();
    if (phrase) return phrase.charAt(0).toUpperCase() + phrase.slice(1);
    return t;
  };

  const summarizeKritikpunkt = (text, maxLen = 60) => {
    if (!text) return "";
    let t = String(text).replace(/\s+/g, " ").replace(/^[-••\s]+/, "").trim();
    if (t.includes("\n")) t = t.split("\n")[0].trim();
    const subject = extractSubjectPhrase(t);
    if (subject && subject.length <= maxLen) return subject;
    if (subject && subject.length > maxLen) t = subject;
    if (t.length <= maxLen) return t;
    const boundaries = [".", "!", "?", ";", ":"];
    for (const b of boundaries) {
      const idx = t.indexOf(b);
      if (idx >= 25 && idx <= maxLen) return t.slice(0, idx + 1).trim();
    }
    const cut = t.lastIndexOf(" ", maxLen);
    if (cut >= 25) return `${t.slice(0, cut).trim()}…`;
    return `${t.slice(0, maxLen).trim()}…`;
  };

  /* ---- data loading ---- */
  useEffect(() => {
    if (!open) return;

    if (propTopic) {
      setModal(propTopic); setError(null); setLoading(false);
      return;
    }

    if (companyId) {
      setLoading(true); setError(null);
      fetch(`${API_URL}/analytics/company/${companyId}/negative-kritikpunkte`)
        .then(async (res) => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
        .then((data) => {
          if (!data.topic) throw new Error("Keine negativen Topics vorhanden");
          setModal({
            title: "Negative Topic",
            topic_label: data.topic, topic: data.topic,
            kritikpunkte: data.kritikpunkte || [],
            avg_rating: data.avg_rating,
            negative_share_percent: data.negative_share_percent,
            categories: data.categories || [data.topic],
          });
        })
        .catch(() => fetch(`${API_URL}/analytics/company/${companyId}/topic-overview`)
          .then((res) => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
          .then((data) => {
            const topics = Array.isArray(data?.topics) ? data.topics : [];
            if (topics.length === 0) { setModal(null); return; }
            const isNeg = (t) => String(t?.sentiment || "").toLowerCase().includes("neg");
            const negativeOnly = topics.filter(isNeg);
            const pool = negativeOnly.length ? negativeOnly : topics;
            const sorted = pool.sort((a, b) => (a.avgRating || 5) - (b.avgRating || 5));
            const most = sorted[0];
            setModal({
              title: "Negative Topic",
              topic_label: most?.topic, topic: most?.topic,
              categories: most?.topic ? [most.topic] : [],
              kritikpunkte: deriveKritikpunkte(most).slice(0, 3),
              avgRating: most?.avgRating, sentiment: most?.sentiment,
            });
          })
        )
        .catch((err) => { setError(err.message || "Fehler beim Laden"); setModal(null); })
        .finally(() => setLoading(false));
    } else {
      setModal(null); setLoading(false); setError(null);
    }
  }, [open, propTopic, companyId]);

  /* ---- derived display values ---- */
  const getTopicLabel = (m) => {
    if (!m) return "—";
    if (m.topic_label) return String(m.topic_label);
    if (m.topic_text)  return String(m.topic_text);
    if (m.topic)       return String(m.topic);
    if (Array.isArray(m.top_words) && m.top_words.length) {
      const w = m.top_words[0];
      return typeof w === "string" ? w : (w?.word ?? "—");
    }
    return "—";
  };

  const getNegativeShare = (m) => {
    if (!m) return null;
    if (m.negative_share_percent != null) {
      const p = Number(m.negative_share_percent);
      return Number.isFinite(p) ? Math.round(p) : null;
    }
    const s = m.sentiments || {};
    const neg = Number(s.negative) || 0, pos = Number(s.positive) || 0, neu = Number(s.neutral) || 0;
    const total = neg + pos + neu;
    if (total > 0) return Math.round((neg / total) * 100);
    if (m.sentiment) {
      const l = String(m.sentiment).toLowerCase();
      if (l.includes("neg")) return 70;
      if (l.includes("neu")) return 45;
      if (l.includes("pos")) return 20;
    }
    const r = m.avgRating ?? m.avg_rating;
    if (r != null && Number.isFinite(Number(r))) {
      return Math.max(0, Math.min(100, Math.round(((5 - Number(r)) / 5) * 100)));
    }
    return null;
  };

  const getKritikpunkte = (m) => {
    if (!m) return [];
    const raw = deriveKritikpunkte(m);
    const points = raw.map((k) => summarizeKritikpunkt(k, 60)).filter(Boolean).slice(0, 4);
    if (points.length) return points;
    if (Array.isArray(m.top_words) && m.top_words.length) {
      return m.top_words.map((w) => summarizeKritikpunkt(typeof w === "string" ? w : w.word, 30))
        .filter(Boolean).slice(0, 4);
    }
    return [];
  };

  const getCategories = (m) => {
    if (!m) return [];
    if (Array.isArray(m.categories) && m.categories.length) return m.categories;
    if (Array.isArray(m.affected_categories) && m.affected_categories.length) return m.affected_categories;
    return [];
  };

  const topicLabel  = getTopicLabel(modal);
  const negShare    = getNegativeShare(modal);
  const kritikp     = getKritikpunkte(modal);
  const categories  = getCategories(modal);
  const avgRating   = modal?.avgRating ?? modal?.avg_rating;

  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      tone="bad"
      icon={<Tag />}
      eyebrow="KENNZAHL · NEGATIVES TOPIC"
      title={loading ? "Lade…" : topicLabel}
      subtitle={
        modal && Number.isFinite(Number(avgRating))
          ? `Ø Rating ${Number(avgRating).toFixed(2).replace(".", ",")} / 5${negShare != null ? ` · ${negShare} % negativ` : ""}`
          : "Topic mit höchster Negativrate"
      }
      size="md"
    >
      {loading && <ModalLoader />}
      {error && <ModalError>Fehler: {error}</ModalError>}
      {!loading && !error && !modal && <ModalEmpty>Keine negativen Topics vorhanden.</ModalEmpty>}

      {!loading && !error && modal && (
        <div className="space-y-3">

          {/* Negative share KPI */}
          {negShare != null && (
            <div className="flex items-center justify-between rounded-md border border-rose-200 bg-rose-50/50 px-3.5 py-2.5">
              <div className="flex items-center gap-2 text-[13px] font-medium text-slate-700">
                <TrendingDown className="h-4 w-4 text-rose-500" />
                Anteil negativer Reviews
              </div>
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[13px] font-semibold bg-rose-500 text-white tnum">
                {negShare} %
              </span>
            </div>
          )}

          {/* Häufige Kritikpunkte */}
          {kritikp.length > 0 && (
            <div className="rounded-md border border-slate-200 bg-white">
              <div className="px-3.5 py-2 border-b border-slate-200 flex items-center gap-2 text-[13px] font-medium text-slate-700">
                <MessageCircle className="h-4 w-4 text-slate-500" />
                Häufige Kritikpunkte
              </div>
              <ul className="divide-y divide-slate-100">
                {kritikp.map((k, i) => (
                  <li key={i} className="flex items-start gap-2.5 px-3.5 py-2.5">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-rose-400 flex-none" aria-hidden="true" />
                    <span className="text-[13px] leading-5 text-slate-800">{k}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Betroffene Kategorien */}
          {categories.length > 0 && (
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3.5 py-2.5">
              <div className="flex items-center gap-2 text-[13px] font-medium text-slate-700 mb-2">
                <Layers className="h-4 w-4 text-slate-500" />
                Betroffene Kategorien
              </div>
              <div className="flex flex-wrap gap-1.5">
                {categories.map((c, i) => (
                  <span
                    key={`${c}-${i}`}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-medium bg-white border border-rose-200 text-rose-700"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </ModalShell>
  );
}
