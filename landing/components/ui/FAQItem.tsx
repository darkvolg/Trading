"use client";

import { useState, useId } from "react";

export function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className={`faq-item border border-border/50 rounded-xl overflow-hidden`}>
      <h3 className="m-0">
        <button
          id={`${id}-trigger`}
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between p-5 text-left hover:bg-card/40 transition-colors"
          aria-expanded={open}
          aria-controls={`${id}-panel`}
        >
          <span className="font-medium text-foreground pr-4">{q}</span>
          <svg
            className={`w-5 h-5 text-primary shrink-0 transition-transform duration-300 ${open ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
          </svg>
        </button>
      </h3>
      <div
        id={`${id}-panel`}
        role="region"
        aria-labelledby={`${id}-trigger`}
        className={`overflow-hidden transition-all duration-300 ${open ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}`}
      >
        <p className="px-5 pb-5 text-muted leading-relaxed text-sm">{a}</p>
      </div>
    </div>
  );
}
