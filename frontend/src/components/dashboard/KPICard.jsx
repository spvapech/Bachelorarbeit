import React from "react";
import { Chevron } from "../../icons";

export default function KPICard({
  id,
  label,
  icon,
  expandedKey,
  onToggle,
  collapsed,
  children,
}) {
  const isExpanded = expandedKey === id;
  const isDimmed = expandedKey !== null && !isExpanded;

  const handleKey = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onToggle(isExpanded ? null : id);
    }
    if (e.key === "Escape" && isExpanded) onToggle(null);
  };

  const stop = (e) => e.stopPropagation();

  return (
    <button
      type="button"
      aria-expanded={isExpanded}
      aria-controls={`${id}-panel`}
      onClick={() => onToggle(isExpanded ? null : id)}
      onKeyDown={handleKey}
      style={{ transition: "border-color 200ms ease, box-shadow 200ms ease, background-color 200ms ease" }}
      className={[
        "group relative w-full text-left bg-white border rounded-lg overflow-hidden",
        "p-4 cursor-pointer outline-none",
        "focus-visible:ring-2 focus-visible:ring-blue-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-50",
        isExpanded ? "md:col-span-2" : "md:col-span-1",
        isExpanded
          ? "border-blue-300 shadow-[0_0_0_4px_rgba(37,99,235,0.06)] bg-gradient-to-b from-[#f5f9ff] to-white cursor-default"
          : "border-slate-200 hover:border-slate-300 hover:shadow-sm",
        isDimmed ? "opacity-80 hover:opacity-100" : "",
      ].join(" ")}
    >
      {/* header */}
      <div className="flex items-center justify-between gap-2 min-h-[18px]">
        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-slate-600 tracking-[0.02em]">
          {icon ? <span className="w-3.5 h-3.5 text-slate-500 flex-none">{icon}</span> : null}
          {label}
        </span>
        <Chevron
          className={[
            "w-3.5 h-3.5 flex-none",
            isExpanded ? "rotate-180 text-blue-600" : "text-slate-400 group-hover:text-blue-500",
          ].join(" ")}
          style={{ transition: "transform 200ms ease" }}
        />
      </div>

      {/* always-visible summary */}
      {collapsed}

      {/* expandable panel */}
      <div
        id={`${id}-panel`}
        role="region"
        aria-label={`${label} Details`}
        className={["collapse-row", isExpanded ? "is-open" : ""].join(" ")}
      >
        <div className="collapse-inner">
          <div
            onClick={stop}
            className="pt-3.5 mt-3.5 border-t border-dashed border-slate-200"
          >
            {children}
          </div>
        </div>
      </div>
    </button>
  );
}
