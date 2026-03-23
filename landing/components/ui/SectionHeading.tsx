"use client";

export function SectionHeading({
  tag,
  title,
  subtitle,
  visible,
}: {
  tag: string;
  title: string;
  subtitle?: string;
  visible?: boolean;
}) {
  return (
    <div className="text-center mb-16">
      <span
        className={`reveal ${visible ? "visible" : ""} inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-5`}
      >
        {tag}
      </span>
      <h2
        className={`reveal reveal-delay-1 ${visible ? "visible" : ""} text-3xl md:text-4xl lg:text-5xl font-bold mb-4 tracking-tight`}
      >
        {title.split(' ').map((word, i) => (
          <span
            key={i}
            className="inline-block opacity-0 translate-y-4 transition-all duration-500"
            style={{
              transitionDelay: visible ? `${i * 0.08 + 0.2}s` : '0s',
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateY(0)' : 'translateY(16px)',
            }}
          >
            {word}{' '}
          </span>
        ))}
      </h2>
      {subtitle && (
        <p
          className={`reveal reveal-delay-2 ${visible ? "visible" : ""} text-muted max-w-2xl mx-auto text-lg leading-relaxed`}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}
