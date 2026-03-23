"use client";

export function SectionDivider({ variant = "default" }: { variant?: "default" | "glow" | "dots" }) {
  if (variant === "glow") {
    return (
      <div className="relative h-px w-full max-w-2xl mx-auto">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/20 to-transparent blur-sm" />
      </div>
    );
  }
  if (variant === "dots") {
    return (
      <div className="flex items-center justify-center gap-2 py-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="w-1.5 h-1.5 rounded-full bg-primary/30" />
        ))}
      </div>
    );
  }
  return (
    <div className="h-px w-full max-w-4xl mx-auto bg-gradient-to-r from-transparent via-border/50 to-transparent" />
  );
}
