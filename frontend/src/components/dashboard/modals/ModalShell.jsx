import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

/* ---- Tone palette — same vocabulary as KPI tiles ---- */
const TONES = {
  good:    { accent: "bg-emerald-500", iconWrap: "bg-emerald-50 text-emerald-600", subtitleColor: "text-emerald-700" },
  warn:    { accent: "bg-amber-500",   iconWrap: "bg-amber-50 text-amber-600",     subtitleColor: "text-amber-700"  },
  bad:     { accent: "bg-rose-500",    iconWrap: "bg-rose-50 text-rose-600",       subtitleColor: "text-rose-700"   },
  info:    { accent: "bg-blue-500",    iconWrap: "bg-blue-50 text-blue-600",       subtitleColor: "text-blue-700"   },
  neutral: { accent: "bg-slate-300",   iconWrap: "bg-slate-100 text-slate-500",    subtitleColor: "text-slate-600"  },
};

/* ============================================================================
   ModalShell — unified surface for all KPI / drilldown dialogs.

   Layout:
     ┌───────────────────────────────────────────┐
     │ [accent bar — top, 3px, tone colour]      │
     │ ┌─icon─┐  EYEBROW                          │
     │ │      │  Title                            │
     │ └──────┘  Subtitle / description           │
     ├───────────────────────────────────────────┤
     │  toolbar (optional: search/filter chips)  │
     ├───────────────────────────────────────────┤
     │  body (caller-provided)                   │
     ├───────────────────────────────────────────┤
     │  footer (optional)                        │
     └───────────────────────────────────────────┘
   ============================================================================ */
export default function ModalShell({
  open,
  onOpenChange,
  tone = "neutral",
  icon = null,
  eyebrow,
  title,
  subtitle,
  toolbar,
  footer,
  size = "md",       // "sm" | "md" | "lg" | "xl"
  children,
}) {
  const t = TONES[tone] ?? TONES.neutral;
  const widthClass = {
    sm: "sm:max-w-md",
    md: "sm:max-w-2xl",
    lg: "sm:max-w-4xl",
    xl: "sm:max-w-6xl",
  }[size] ?? "sm:max-w-2xl";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={[
          "p-0 gap-0 overflow-hidden rounded-xl border-slate-200",
          "max-h-[88vh] overflow-y-auto",
          "w-[calc(100vw-2rem)]",
          widthClass,
        ].join(" ")}
      >
        {/* Tonal accent bar at top */}
        <span aria-hidden="true" className={["block h-[3px] w-full", t.accent].join(" ")} />

        {/* Header */}
        <DialogHeader className="px-6 pt-5 pb-4 pr-14 border-b border-slate-200 bg-white">
          <div className="flex items-start gap-3">
            {icon && (
              <span className={["w-9 h-9 rounded-lg grid place-items-center flex-none", t.iconWrap].join(" ")}>
                <span className="w-[18px] h-[18px]">{icon}</span>
              </span>
            )}
            <div className="flex-1 min-w-0 text-left">
              {eyebrow && (
                <p className="m-0 mb-1 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">
                  {eyebrow}
                </p>
              )}
              <DialogTitle className="text-[18px] leading-6 font-semibold tracking-tight text-slate-900 m-0">
                {title}
              </DialogTitle>
              {subtitle && (
                <DialogDescription className={["text-[13px] mt-1 leading-5", t.subtitleColor].join(" ")}>
                  {subtitle}
                </DialogDescription>
              )}
            </div>
          </div>
        </DialogHeader>

        {/* Optional toolbar (search/filter chips) */}
        {toolbar && (
          <div className="px-6 py-3 border-b border-slate-200 bg-slate-50">
            {toolbar}
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-5 bg-white">
          {children}
        </div>

        {/* Optional footer */}
        {footer && (
          <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
            {footer}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

/* ============================================================================
   Loading / Error / Empty states for inside the modal body
   ============================================================================ */
export function ModalLoader({ label = "Lade Daten…" }) {
  return (
    <div className="py-12 text-center text-[13px] text-slate-500" aria-live="polite">
      <div className="inline-flex items-center gap-2">
        <div className="h-4 w-4 border-2 border-slate-200 border-t-slate-600 rounded-full animate-spin" />
        {label}
      </div>
    </div>
  );
}

export function ModalError({ children }) {
  return (
    <div className="py-8 px-4 text-center text-[13px] text-rose-700 bg-rose-50 border border-rose-200 rounded-md">
      {children}
    </div>
  );
}

export function ModalEmpty({ children }) {
  return (
    <div className="py-12 text-center text-[13px] text-slate-500">
      {children}
    </div>
  );
}
