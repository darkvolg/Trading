export function TechStackLogos({ visible, label }: { visible: boolean; label: string }) {
  const stack = [
    { name: "Freqtrade", desc: "Trading Engine", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" /></svg>
    )},
    { name: "Python", desc: "Strategy Logic", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M9.585 11.692h4.328s2.432.039 2.432-2.35V5.391S16.714 3 11.936 3C7.362 3 7.647 4.983 7.647 4.983l.006 2.055h4.363v.617H5.92s-2.927-.332-2.927 4.282 2.555 4.45 2.555 4.45h1.524v-2.141s-.083-2.554 2.513-2.554zm-.056-5.74a.784.784 0 1 1 0-1.57.784.784 0 0 1 0 1.57z" /><path d="M18.452 7.532h-1.524v2.141s.083 2.554-2.513 2.554h-4.328s-2.432-.04-2.432 2.35v3.951s-.369 2.391 4.409 2.391c4.573 0 4.288-1.983 4.288-1.983l-.006-2.054h-4.363v-.618h6.096s2.927.332 2.927-4.282c0-4.614-2.554-4.45-2.554-4.45zm-4.597 10.455a.784.784 0 1 1 0 1.57.784.784 0 0 1 0-1.57z" /></svg>
    )},
    { name: "Telegram", desc: "Signal Delivery", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" /></svg>
    )},
    { name: "Cornix", desc: "Auto-Execution", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" /><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" fill="none" stroke="currentColor" strokeWidth="1" /></svg>
    )},
    { name: "Google Sheets", desc: "Public Tracking", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M19 11V9h-6V5h-2v4H5v2h6v4h2v-4h6z" opacity="0.5" /><path d="M3 5v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2zm2 0h14v14H5V5z" /><rect x="7" y="8" width="4" height="2" rx="0.5" /><rect x="13" y="8" width="4" height="2" rx="0.5" /><rect x="7" y="12" width="4" height="2" rx="0.5" /><rect x="13" y="12" width="4" height="2" rx="0.5" /><rect x="7" y="16" width="4" height="2" rx="0.5" /><rect x="13" y="16" width="4" height="2" rx="0.5" /></svg>
    )},
  ];
  return (
    <section className="py-12 px-4 border-y border-border/20 bg-card/10">
      <div className="max-w-5xl mx-auto">
        <p className={`reveal ${visible ? "visible" : ""} text-center text-muted text-[11px] uppercase tracking-[0.25em] font-mono mb-8`}>
          {label}
        </p>
        <div className={`reveal reveal-delay-1 ${visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-8 md:gap-14`}>
          {stack.map((s) => (
            <div key={s.name} className="flex items-center gap-2.5 opacity-40 hover:opacity-70 transition-opacity duration-300 cursor-default group">
              <div className="w-9 h-9 rounded-lg border border-border/30 bg-card/50 flex items-center justify-center text-primary/70 group-hover:text-primary group-hover:border-primary/30 transition-all">
                {s.icon}
              </div>
              <div>
                <span className="font-mono text-xs text-foreground/70 tracking-wider block leading-tight">{s.name}</span>
                <span className="text-[10px] text-muted">{s.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
