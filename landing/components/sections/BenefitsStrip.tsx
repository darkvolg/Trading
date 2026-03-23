import type { TStrings } from "@/lib/i18n";

export function BenefitsStrip({ t, visible }: { t: TStrings; visible: boolean }) {
  const benefits = [
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 0 1-6.364 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" />
      </svg>
    ), label: t.benefit1 },
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ), label: t.benefit2 },
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ), label: t.benefit3 },
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
      </svg>
    ), label: t.benefit4 },
  ];
  return (
    <div className={`reveal ${visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-6 md:gap-10 py-8`}>
      {benefits.map((b, i) => (
        <div key={i} className="flex items-center gap-2 text-primary/80">
          <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
            {b.icon}
          </div>
          <span className="text-sm font-medium text-foreground/70">{b.label}</span>
        </div>
      ))}
    </div>
  );
}
