import React from "react";

export function Delta({ tone = "neu", icon, children, className = "" }) {
  const map = {
    pos:  "bg-emerald-50 text-emerald-700",
    neg:  "bg-rose-50 text-rose-700",
    warn: "bg-amber-50 text-amber-700",
    neu:  "bg-slate-100 text-slate-600",
  };
  return (
    <span
      className={[
        "inline-flex items-center gap-1 whitespace-nowrap",
        "px-1.5 py-[3px] rounded-full text-[12px] font-medium leading-none",
        map[tone] ?? map.neu,
        className,
      ].join(" ")}
    >
      {icon ? <span className="w-3 h-3 flex-none">{icon}</span> : null}
      {children}
    </span>
  );
}

export function Skeleton() {
  return (
    <div className="flex flex-col gap-2 py-1" aria-hidden="true">
      <div className="skeleton h-2.5 w-1/2" />
      <div className="skeleton h-2.5 w-[90%]" />
      <div className="skeleton h-2.5 w-[70%]" />
      <div className="skeleton h-2.5 w-[90%]" />
    </div>
  );
}

export function SectionTitle({ children, className = "" }) {
  return (
    <p
      className={[
        "font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 mb-2 mt-0",
        className,
      ].join(" ")}
    >
      {children}
    </p>
  );
}

export function StatList({ items }) {
  return (
    <div className="flex flex-col">
      {items.map((it, i) => (
        <div
          key={it.k}
          className={[
            "flex items-baseline justify-between text-[12px] py-1",
            i < items.length - 1 ? "border-b border-dashed border-slate-200" : "",
          ].join(" ")}
        >
          <span className="text-slate-600">{it.k}</span>
          <span className={["font-semibold tnum", it.tone || "text-slate-900"].join(" ")}>
            {it.v}
          </span>
        </div>
      ))}
    </div>
  );
}

export function CTALink({ onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "inline-flex items-center gap-1.5 text-[12px] font-medium",
        "text-blue-700 bg-blue-50 border border-blue-600/20",
        "px-2.5 py-1.5 rounded-md cursor-pointer",
        "transition-colors duration-150",
        "hover:bg-blue-100 hover:text-blue-800",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
