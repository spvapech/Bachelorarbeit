import * as React from "react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import {
  Calendar, User, Star,
  ThumbsUp, ThumbsDown, Lightbulb,
  Briefcase, FileText, ChevronLeft, ChevronRight, MessageSquare,
} from "lucide-react"

/* ─── Helpers ─── */
const fmt = (n, d = 1) =>
  Number.isFinite(Number(n)) ? Number(n).toFixed(d).replace(".", ",") : "—"

const formatDate = (dateString) => {
  if (!dateString) return "Unbekannt"
  try {
    return new Date(dateString).toLocaleDateString("de-DE", {
      year: "numeric", month: "long", day: "numeric",
    })
  } catch { return "Unbekannt" }
}

const formatStatus = (status) => {
  if (!status) return null
  const s = String(status).trim()
  if (s === "1" || s === "1.0") return "Angestellt"
  if (s === "0" || s === "0.0") return "Ex-Angestellt"
  const normalized = s.toLowerCase().replace(/\s+/g, "-")
  if (/^ex-?angestell/i.test(normalized)) return "Ex-Angestellt"
  return s
}

const ratingTone = (s) => {
  const n = Number(s)
  if (!Number.isFinite(n)) return {
    text: "text-slate-700", bar: "bg-slate-300", bg: "bg-slate-50",
    border: "border-slate-200", hoverBorder: "hover:border-slate-300",
    gradient: "bg-white", labelText: "text-slate-600",
  }
  if (n >= 3.5) return {
    text: "text-emerald-700", bar: "bg-emerald-500", bg: "bg-emerald-50",
    border: "border-emerald-200", hoverBorder: "hover:border-emerald-400",
    gradient: "bg-gradient-to-r from-emerald-50/70 to-white",
    labelText: "text-emerald-700",
  }
  if (n >= 2.5) return {
    text: "text-amber-700", bar: "bg-amber-500", bg: "bg-amber-50",
    border: "border-amber-200", hoverBorder: "hover:border-amber-400",
    gradient: "bg-gradient-to-r from-amber-50/70 to-white",
    labelText: "text-amber-700",
  }
  return {
    text: "text-rose-700", bar: "bg-rose-500", bg: "bg-rose-50",
    border: "border-rose-200", hoverBorder: "hover:border-rose-400",
    gradient: "bg-gradient-to-r from-rose-50/70 to-white",
    labelText: "text-rose-700",
  }
}

const ratingCategories = [
  { key: "arbeitsatmosphaere",         label: "Arbeitsatmosphäre" },
  { key: "image",                       label: "Image" },
  { key: "work_life_balance",           label: "Work-Life Balance" },
  { key: "karriere_weiterbildung",      label: "Karriere/Weiterbildung" },
  { key: "gehalt_sozialleistungen",     label: "Gehalt/Sozialleistungen" },
  { key: "kollegenzusammenhalt",        label: "Kollegenzusammenhalt" },
  { key: "umwelt_sozialbewusstsein",    label: "Umwelt-/Sozialbewusstsein" },
  { key: "vorgesetztenverhalten",       label: "Vorgesetztenverhalten" },
  { key: "kommunikation",               label: "Kommunikation" },
  { key: "interessante_aufgaben",       label: "Interessante Aufgaben" },
  { key: "umgang_mit_aelteren_kollegen", label: "Umgang mit älteren Kollegen" },
  { key: "arbeitsbedingungen",          label: "Arbeitsbedingungen" },
  { key: "gleichberechtigung",          label: "Gleichberechtigung" },
]

/* ─── Star rendering ─── */
function StarRating({ rating, size = "md" }) {
  if (rating === null || rating === undefined) {
    return <span className="text-[12px] text-slate-400 italic">Nicht bewertet</span>
  }
  const rounded = Math.round(rating * 2) / 2
  const fullStars = Math.floor(rounded)
  const hasHalf = rounded % 1 !== 0
  const empty = 5 - fullStars - (hasHalf ? 1 : 0)
  const px = size === "sm" ? 12 : size === "lg" ? 20 : 16

  return (
    <div className="inline-flex items-center gap-0.5">
      {[...Array(fullStars)].map((_, i) => (
        <Star key={`f${i}`} style={{ width: px, height: px }} className="fill-amber-400 text-amber-400" strokeWidth={1.5} />
      ))}
      {hasHalf && (
        <span className="relative inline-block" style={{ width: px, height: px }}>
          <Star style={{ width: px, height: px }} className="absolute inset-0 fill-slate-200 text-slate-300" strokeWidth={1.5} />
          <span className="absolute inset-0 overflow-hidden" style={{ width: "50%" }}>
            <Star style={{ width: px, height: px }} className="fill-amber-400 text-amber-400" strokeWidth={1.5} />
          </span>
        </span>
      )}
      {[...Array(empty)].map((_, i) => (
        <Star key={`e${i}`} style={{ width: px, height: px }} className="fill-slate-200 text-slate-300" strokeWidth={1.5} />
      ))}
    </div>
  )
}

/* ─── Section block (gleich wie TopicDetailModal) ─── */
function Section({ icon, title, eyebrow, tone = "neutral", action, children }) {
  const toneMap = {
    good:    { iconBg: "bg-emerald-50",   iconText: "text-emerald-600", border: "border-emerald-200", titleColor: "text-emerald-700" },
    bad:     { iconBg: "bg-rose-50",      iconText: "text-rose-600",    border: "border-rose-200",    titleColor: "text-rose-700" },
    info:    { iconBg: "bg-blue-50",      iconText: "text-blue-600",    border: "border-blue-200",    titleColor: "text-blue-700" },
    warn:    { iconBg: "bg-amber-50",     iconText: "text-amber-600",   border: "border-amber-200",   titleColor: "text-amber-700" },
    neutral: { iconBg: "bg-slate-100",    iconText: "text-slate-600",   border: "border-slate-200",   titleColor: "text-slate-900" },
  }
  const t = toneMap[tone] ?? toneMap.neutral
  return (
    <section className={`bg-white border ${t.border} rounded-lg overflow-hidden shadow-xs`}>
      <header className="px-4 py-3 border-b border-slate-200 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {icon && (
            <span className={`w-7 h-7 rounded-md grid place-items-center flex-none ${t.iconBg} ${t.iconText} [&_svg]:w-[14px] [&_svg]:h-[14px]`}>
              {icon}
            </span>
          )}
          <div className="min-w-0">
            {eyebrow && (
              <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{eyebrow}</p>
            )}
            <h3 className={`m-0 text-[14px] leading-5 font-semibold tracking-tight ${t.titleColor}`}>{title}</h3>
          </div>
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </header>
      <div className="p-4">{children}</div>
    </section>
  )
}

/* ============================================================================
   ReviewDetailModal
   ============================================================================ */
export default function ReviewDetailModal({
  open, onOpenChange, reviewDetail, allReviewDetails = [], currentIndex = 0, onNavigate,
}) {
  if (!reviewDetail || !reviewDetail.fullReview) return null

  const { fullReview } = reviewDetail
  const hasMultiple = allReviewDetails.length > 1
  const canPrev = currentIndex > 0
  const canNext = currentIndex < allReviewDetails.length - 1
  const overall = Number(fullReview.durchschnittsbewertung)
  const overallTone = ratingTone(overall)

  const goPrev = () => canPrev && onNavigate?.(currentIndex - 1)
  const goNext = () => canNext && onNavigate?.(currentIndex + 1)

  const formatText = (text) => {
    if (!text) return null
    return text.split("\n").map((line, i, arr) => (
      <span key={i}>
        {line}
        {i < arr.length - 1 && <br />}
      </span>
    ))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="overflow-hidden flex flex-col p-0 gap-0"
        style={{ width: "82vw", maxWidth: "82vw", height: "88vh", maxHeight: "88vh" }}
      >
        {/* Tonaler Akzentbalken oben (basierend auf Gesamtbewertung) */}
        <span aria-hidden="true" className={`block h-[3px] w-full ${overallTone.bar}`} />

        {/* ── Header ── */}
        <DialogTitle className="sr-only">{fullReview.titel || "Review Details"}</DialogTitle>
        <div className="px-5 py-3 pr-14 border-b border-slate-200 flex items-center justify-between gap-3 flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className={`w-7 h-7 rounded-md grid place-items-center flex-none ${overallTone.bg} ${overallTone.text} [&_svg]:w-[14px] [&_svg]:h-[14px]`}>
              <MessageSquare />
            </span>
            <div className="flex items-center gap-x-3 gap-y-1 flex-wrap min-w-0">
              <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none flex-none">
                EINZEL-REVIEW · DETAIL
              </p>
              <span className="text-slate-300 text-[10px]">·</span>
              <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 [&_svg]:w-3 [&_svg]:h-3">
                <Calendar />
                {formatDate(fullReview.datum)}
              </span>
              <span className="text-slate-300 text-[10px]">·</span>
              <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 [&_svg]:w-3 [&_svg]:h-3">
                <User />
                {fullReview.sourceType || "Unbekannt"}
              </span>
              {fullReview.status && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[10.5px] uppercase tracking-wider">
                  {formatStatus(fullReview.status)}
                </span>
              )}
            </div>
          </div>

          {/* Navigation */}
          {hasMultiple && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="font-mono text-[11px] tnum text-slate-500">
                {currentIndex + 1} / {allReviewDetails.length}
              </span>
              <div className="inline-flex">
                <button
                  onClick={goPrev}
                  disabled={!canPrev}
                  className="h-7 w-7 inline-flex items-center justify-center rounded-l-md border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-40 disabled:cursor-not-allowed [&_svg]:w-3.5 [&_svg]:h-3.5"
                  title="Vorherige Review"
                >
                  <ChevronLeft />
                </button>
                <button
                  onClick={goNext}
                  disabled={!canNext}
                  className="h-7 w-7 inline-flex items-center justify-center rounded-r-md border border-l-0 border-slate-300 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-40 disabled:cursor-not-allowed [&_svg]:w-3.5 [&_svg]:h-3.5"
                  title="Nächste Review"
                >
                  <ChevronRight />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Body (scrollable) ── */}
        <div className="flex-1 overflow-y-auto bg-slate-50">
          <div className="p-5 space-y-4">

            {/* Gesamtbewertung — prominent */}
            {Number.isFinite(overall) && (
              <div className={`bg-white border ${overallTone.border} rounded-lg overflow-hidden shadow-xs`}>
                <div className="px-5 py-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`w-10 h-10 rounded-md grid place-items-center flex-none ${overallTone.bg} ${overallTone.text} [&_svg]:w-5 [&_svg]:h-5`}>
                      <Star className="fill-current" />
                    </span>
                    <div>
                      <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                        GESAMTBEWERTUNG
                      </p>
                      <StarRating rating={overall} size="lg" />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`m-0 text-[36px] font-semibold tnum tracking-tight leading-none ${overallTone.text}`}>
                      {fmt(overall, 1)}
                    </p>
                    <p className="m-0 mt-1 text-[11px] text-slate-500 tnum">von 5,0</p>
                  </div>
                </div>
                {/* Tonaler Fortschrittsbalken am unteren Rand */}
                <div className="h-1 bg-slate-100">
                  <div className={`h-full ${overallTone.bar}`} style={{ width: `${(overall / 5) * 100}%` }} />
                </div>
              </div>
            )}

            {/* Review-Texte: alle Textfelder im gemeinsamen Raster */}
            {(fullReview.titel || fullReview.gut_am_arbeitgeber || fullReview.schlecht_am_arbeitgeber || fullReview.verbesserungsvorschlaege || fullReview.stellenbeschreibung || fullReview.jobbeschreibung || fullReview.sourceType === "Mitarbeiter") && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Zeile 1: Titel | Stellenbeschreibung (Bewerber) oder Jobbeschreibung (Mitarbeiter) */}
                {fullReview.titel && (
                  <Section icon={<FileText />} eyebrow="TITEL" title="Review-Titel">
                    <p className="m-0 text-[14px] font-medium text-slate-800 leading-snug">
                      {fullReview.titel}
                    </p>
                  </Section>
                )}

                {fullReview.stellenbeschreibung && (
                  <Section icon={<FileText />} eyebrow="POSITION" title="Stellenbeschreibung">
                    <p className="m-0 text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {formatText(fullReview.stellenbeschreibung)}
                    </p>
                  </Section>
                )}

                {fullReview.jobbeschreibung && (
                  <Section icon={<Briefcase />} eyebrow="JOB" title="Jobbeschreibung">
                    <p className="m-0 text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {formatText(fullReview.jobbeschreibung)}
                    </p>
                  </Section>
                )}

                {/* Zeile 2: Gut | Schlecht */}
                <Section icon={<ThumbsUp />} eyebrow="POSITIV" title="Gut am Arbeitgeber" tone="good">
                  {fullReview.gut_am_arbeitgeber ? (
                    <p className="m-0 text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {formatText(fullReview.gut_am_arbeitgeber)}
                    </p>
                  ) : (
                    <p className="m-0 text-[13px] text-slate-400 italic">Keine Angabe</p>
                  )}
                </Section>

                <Section icon={<ThumbsDown />} eyebrow="NEGATIV" title="Schlecht am Arbeitgeber" tone="bad">
                  {fullReview.schlecht_am_arbeitgeber ? (
                    <p className="m-0 text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {formatText(fullReview.schlecht_am_arbeitgeber)}
                    </p>
                  ) : (
                    <p className="m-0 text-[13px] text-slate-400 italic">Keine Angabe</p>
                  )}
                </Section>

                {/* Verbesserungsvorschläge */}
                {fullReview.verbesserungsvorschlaege && (
                  <Section icon={<Lightbulb />} eyebrow="VORSCHLÄGE" title="Verbesserungsvorschläge" tone="info">
                    <p className="m-0 text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {formatText(fullReview.verbesserungsvorschlaege)}
                    </p>
                  </Section>
                )}
              </div>
            )}

            {/* Detaillierte Sterne-Bewertungen — KPI-Karten-Look */}
            {fullReview.ratings && Object.values(fullReview.ratings).some((r) => r != null) && (
              <Section icon={<Star />} eyebrow="KATEGORIEN" title="Detaillierte Bewertungen">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {ratingCategories.map(({ key, label }) => {
                    const rating = fullReview.ratings[key]
                    if (rating === null || rating === undefined) return null
                    const t = ratingTone(rating)
                    return (
                      <div
                        key={key}
                        className={[
                          "relative flex items-center justify-between gap-3 pl-4 pr-3 py-2.5 rounded-md border overflow-hidden transition-all",
                          t.border, t.hoverBorder, t.gradient, "hover:shadow-sm",
                        ].join(" ")}
                      >
                        {/* Linker Akzentbalken — gleich wie KPI-Karten */}
                        <span aria-hidden="true" className={`absolute left-0 top-0 bottom-0 w-[3px] ${t.bar}`} />

                        <span className={`text-[12.5px] font-medium truncate ${t.labelText}`} title={label}>
                          {label}
                        </span>
                        <div className="flex items-center gap-2 flex-none">
                          <StarRating rating={rating} size="sm" />
                          <span className={`font-semibold tnum text-[14px] min-w-[32px] text-right ${t.text}`}>
                            {fmt(rating, 1)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Section>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
