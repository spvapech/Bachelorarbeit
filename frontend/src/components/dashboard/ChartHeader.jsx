import React from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, Maximize2 } from "lucide-react";

/* ============================================================================
   ChartCardHeader — sticky header for chart cards.

   Layout:
   - `inlineActions=true` (modal): Title and actions sit on one row.
   - `inlineActions=false` (card / compact): Title row only.
       The actions row is rendered separately by the parent below the title.
   ============================================================================ */
export function ChartCardHeader({
  icon,
  eyebrow,
  title,
  subtitle,
  expandable,
  actions,            // node | null
  inlineActions = false,
}) {
  return (
    <div
      className="px-4 pt-3 pb-3 border-b border-slate-200 bg-white"
      style={{ borderTopLeftRadius: 10, borderTopRightRadius: 10 }}
    >
      {/* Top row: icon + title (+ inline actions in modal mode) */}
      <div className={["flex gap-3", inlineActions ? "items-start justify-between" : "items-start"].join(" ")}>
        <div className="flex items-start gap-2.5 min-w-0 flex-1">
          {icon && (
            <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 mt-0.5">
              <span className="w-[14px] h-[14px]">{icon}</span>
            </span>
          )}
          <div className="min-w-0 flex-1">
            {eyebrow && (
              <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                {eyebrow}
              </p>
            )}
            <h3 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900 inline-flex items-center gap-1.5">
              {title}
              {expandable && (
                <Maximize2 className="h-3 w-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </h3>
            {subtitle && (
              <p className="m-0 mt-0.5 text-[11px] text-slate-500 leading-4 truncate">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Inline actions (modal mode) */}
        {inlineActions && actions && (
          <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 flex-wrap justify-end flex-shrink-0">
            {actions}
          </div>
        )}
      </div>

      {/* Second row actions (card / compact mode) */}
      {!inlineActions && actions && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="flex items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 flex-wrap"
        >
          {actions}
        </div>
      )}
    </div>
  );
}

/* ============================================================================
   SourceToggle
   - compact=true: nur Farbpunkte (Tooltip zeigt Label)
   - compact=false: Punkt + Label
   ============================================================================ */
export function SourceToggle({ value, onChange, options, compact = false }) {
  return (
    <div
      role="tablist"
      className="inline-flex bg-slate-100 border border-slate-200 rounded-md p-0.5"
    >
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            role="tab"
            aria-selected={active}
            title={opt.label}
            onClick={() => onChange(opt.value)}
            className={[
              compact ? "h-6 px-2 rounded-[5px]" : "h-7 px-3 rounded-[5px]",
              "flex items-center gap-1.5 text-[12px] font-medium transition-colors",
              active
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900",
            ].join(" ")}
          >
            <span
              className="w-1.5 h-1.5 rounded-full flex-none"
              style={{ background: opt.color }}
              aria-hidden="true"
            />
            {!compact && <span>{opt.label}</span>}
            {compact && <span className="text-[11px]">{opt.label.slice(0, 2)}</span>}
          </button>
        );
      })}
    </div>
  );
}

/* ============================================================================
   DropdownPicker
   - compact=true: Icon + Wert (kein Label-Prefix, kompakteres Padding)
   - compact=false: Icon + "Label:" + Wert
   ============================================================================ */
export function DropdownPicker({
  label,
  value,
  options,
  onChange,
  icon,
  align = "end",
  className = "",
  compact = false,
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          title={label ? `${label}: ${value}` : value}
          className={[
            "h-7 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium",
            "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50",
            "transition-colors",
            compact ? "px-2" : "px-2.5",
            "[&_svg]:flex-none [&_svg]:w-3.5 [&_svg]:h-3.5",
            className,
          ].join(" ")}
        >
          {icon && <span className="text-slate-500 inline-flex items-center justify-center flex-none">{icon}</span>}
          {!compact && label && <span className="text-slate-500">{label}:</span>}
          <span className="text-slate-900 truncate max-w-[140px]">{value}</span>
          <ChevronDown className="text-slate-400" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="min-w-[140px]">
        {options.length === 0 ? (
          <DropdownMenuItem disabled className="text-[12px]">Keine Daten</DropdownMenuItem>
        ) : (
          options.map((opt) => (
            <DropdownMenuItem
              key={String(opt.value)}
              onClick={() => onChange(opt.value)}
              className="text-[12px]"
            >
              {opt.label}
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
