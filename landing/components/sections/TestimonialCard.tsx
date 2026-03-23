export function TestimonialCard({ quote, author, role, delay, visible }: { quote: string; author: string; role: string; delay: number; visible: boolean }) {
  return (
    <div className={`reveal reveal-delay-${delay} ${visible ? "visible" : ""} testimonial-card p-6 rounded-2xl border border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/20 transition-all`}>
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <svg key={i} className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
      <p className="text-foreground/90 text-sm leading-relaxed mb-4 italic">&ldquo;{quote}&rdquo;</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/30 to-primary/10 flex items-center justify-center text-primary font-bold text-sm">
          {author.charAt(0)}
        </div>
        <div>
          <div className="text-sm font-semibold text-foreground">{author}</div>
          <div className="text-xs text-muted">{role}</div>
        </div>
      </div>
    </div>
  );
}
