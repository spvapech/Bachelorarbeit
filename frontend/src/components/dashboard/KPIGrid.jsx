import React from "react";
import { Delta } from "../ui/primitives";
import { Star, TrendUp, TrendDown, Alert, Tag } from "../../icons";

const fmt = (n, d = 1) => (isNaN(Number(n)) ? "—" : Number(n).toFixed(d).replace(".", ","));

/* ---- Tonal palette ---------------------------------------------------------
   Each tone defines how the tile reads at a glance:
   - 'good':    emerald (positive performance)
   - 'warn':    amber   (mid-range / monitor)
   - 'bad':     rose    (critical / needs action)
   - 'neutral': slate   (no data / flat)
--------------------------------------------------------------------------- */
const TONES = {
  good: {
    border: "border-emerald-200",
    hoverBorder: "hover:border-emerald-400",
    accent: "bg-emerald-500",
    bg: "bg-gradient-to-b from-emerald-50/70 to-white",
    iconWrap: "bg-emerald-50 text-emerald-600",
    label: "text-emerald-700",
    value: "text-emerald-700",
  },
  warn: {
    border: "border-amber-200",
    hoverBorder: "hover:border-amber-400",
    accent: "bg-amber-500",
    bg: "bg-gradient-to-b from-amber-50/70 to-white",
    iconWrap: "bg-amber-50 text-amber-600",
    label: "text-amber-700",
    value: "text-amber-700",
  },
  bad: {
    border: "border-rose-200",
    hoverBorder: "hover:border-rose-400",
    accent: "bg-rose-500",
    bg: "bg-gradient-to-b from-rose-50/70 to-white",
    iconWrap: "bg-rose-50 text-rose-600",
    label: "text-rose-700",
    value: "text-rose-700",
  },
  neutral: {
    border: "border-slate-200",
    hoverBorder: "hover:border-slate-300",
    accent: "bg-slate-300",
    bg: "bg-white",
    iconWrap: "bg-slate-100 text-slate-500",
    label: "text-slate-600",
    value: "text-slate-900",
  },
};

/* ---- Score → tone mapping (Ø Score & Most Critical) -------------------- */
const scoreTone = (s) => {
  const n = Number(s);
  if (!Number.isFinite(n)) return "neutral";
  if (n >= 3.5) return "good";
  if (n >= 2.5) return "warn";
  return "bad";
};

/* ---- Trend → tone mapping ---------------------------------------------- */
const trendTone = (sign) => {
  if (sign === "up") return "good";
  if (sign === "down") return "bad";
  return "neutral";
};

/* ============================================================================
   Single KPI tile
   ============================================================================ */
function KPITile({ label, icon, value, valueSize = "lg", delta, footer, tone = "neutral", onClick, disabled }) {
  const t = TONES[tone] ?? TONES.neutral;
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      className={[
        "relative group w-full text-left rounded-lg overflow-hidden",
        "border px-4 py-3.5",
        t.border, t.bg,
        disabled ? "cursor-not-allowed opacity-60" : ["cursor-pointer hover:shadow-sm", t.hoverBorder].join(" "),
      ].join(" ")}
      style={{ transition: "border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease" }}
    >
      {/* tone accent bar */}
      <span
        aria-hidden="true"
        className={["absolute left-0 top-0 bottom-0 w-[3px]", t.accent].join(" ")}
      />

      {/* header */}
      <div className="flex items-center justify-between gap-2 min-h-[18px]">
        <span className={["inline-flex items-center gap-1.5 text-[11px] font-medium tracking-[0.02em]", t.label].join(" ")}>
          {icon ? (
            <span className={["w-4 h-4 rounded-md grid place-items-center flex-none", t.iconWrap].join(" ")}>
              <span className="w-3 h-3">{icon}</span>
            </span>
          ) : null}
          {label}
        </span>
        <span
          className="text-[10px] font-medium text-slate-400 group-hover:text-slate-700"
          style={{ transition: "color 150ms ease" }}
        >
          Details →
        </span>
      </div>

      {/* value + delta */}
      <div className="flex items-baseline justify-between gap-3 mt-2.5">
        <span
          className={[
            "font-semibold tnum tracking-tight truncate",
            t.value,
            valueSize === "lg" ? "text-[32px] leading-9" : "text-[18px] leading-6",
          ].join(" ")}
        >
          {value}
        </span>
        {delta}
      </div>

      {/* footer */}
      {footer && (
        <span className="block text-[11px] text-slate-500 mt-1">{footer}</span>
      )}
    </button>
  );
}

/* ============================================================================
   KPIGrid — 4 colour-coded tiles. Each one pops a modal.
   ============================================================================ */
export default function KPIGrid({
  companyId,
  avgScore,
  avgCount,
  trendData,
  mostCriticalData,
  negativeTopicItem,
  getNegativeTopicName,
  onOpenScore,
  onOpenTrend,
  onOpenCritical,
  onOpenNegative,
  topicOverviewRef,
}) {
  const negName = getNegativeTopicName(negativeTopicItem);

  const avgT     = avgScore != null ? scoreTone(avgScore) : "neutral";
  const avgDelta = avgScore != null
    ? <Delta tone={avgT === "good" ? "pos" : avgT === "bad" ? "neg" : "warn"}>/ 5</Delta>
    : <Delta tone="neu">/ 5</Delta>;

  const trendDelta = trendData ? parseFloat(trendData.avgDelta) : null;
  const trendT     = trendTone(trendData?.sign);

  // Most-Critical tile is always "bad" once data exists — that's the whole
  // point of the metric. If no data: neutral.
  const criticalT = mostCriticalData ? scoreTone(mostCriticalData.score) : "neutral";

  // Negative-Topic tile is also always 'bad' when present.
  const negativeT = negativeTopicItem ? "bad" : "neutral";

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">

      {/* Ø Score */}
      <KPITile
        label="Ø Score"
        icon={<Star />}
        tone={avgT}
        value={avgScore ? fmt(avgScore) : "—"}
        delta={avgDelta}
        footer={avgCount ? `n = ${Number(avgCount).toLocaleString("de-DE")}` : "alle Quellen"}
        disabled={!companyId}
        onClick={onOpenScore}
      />

      {/* Trend */}
      <KPITile
        label={trendData?.windowMonths ? `Trend ${trendData.windowMonths}M` : "Trend"}
        icon={trendData?.sign === "down" ? <TrendDown /> : <TrendUp />}
        tone={trendT}
        value={
          trendDelta !== null
            ? `${trendDelta > 0 ? "+" : ""}${fmt(trendDelta, 1)}`
            : "—"
        }
        delta={
          trendData ? (
            <Delta
              tone={trendT === "good" ? "pos" : trendT === "bad" ? "neg" : "neu"}
              icon={trendData.sign === "up" ? <TrendUp /> : trendData.sign === "down" ? <TrendDown /> : null}
            >
              {trendData.sign === "up" ? "steigend" : trendData.sign === "down" ? "sinkend" : "stabil"}
            </Delta>
          ) : null
        }
        footer={trendData?.windowMonths ? `vs. Vorperiode (${trendData.windowMonths} Mon.)` : "vs. Vorperiode"}
        disabled={!companyId}
        onClick={onOpenTrend}
      />

      {/* Most Critical */}
      <KPITile
        label="Most Critical"
        icon={<Alert />}
        tone={criticalT}
        value={mostCriticalData?.topicName ?? "—"}
        valueSize="sm"
        delta={mostCriticalData ? (
          <Delta tone={criticalT === "good" ? "pos" : criticalT === "warn" ? "warn" : "neg"}>
            {fmt(mostCriticalData.score)} / 5
          </Delta>
        ) : null}
        footer="niedrigster Topic-Score"
        disabled={!companyId}
        onClick={onOpenCritical}
      />

      {/* Negative Topic */}
      <KPITile
        label="Negative Topic"
        icon={<Tag />}
        tone={negativeT}
        value={negName !== "-" ? negName : "—"}
        valueSize="sm"
        delta={
          negativeTopicItem?.mention_count
            ? <Delta tone="neg">n = {negativeTopicItem.mention_count}</Delta>
            : null
        }
        footer="höchste Negativrate"
        disabled={!companyId}
        onClick={() => {
          if (negName && negName !== "-" && topicOverviewRef?.current?.openTopicByName) {
            topicOverviewRef.current.openTopicByName(negName);
          } else {
            onOpenNegative();
          }
        }}
      />
    </div>
  );
}
