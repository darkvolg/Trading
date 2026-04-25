import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const alt = "TrendRider — Algorithmic Crypto Trading Signals";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "sans-serif",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Background grid pattern */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(rgba(0,212,170,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,170,0.05) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />

        {/* Glow effects */}
        <div
          style={{
            position: "absolute",
            top: "-20%",
            left: "30%",
            width: "500px",
            height: "500px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(0,212,170,0.12) 0%, transparent 70%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "-10%",
            right: "20%",
            width: "400px",
            height: "400px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(255,215,0,0.08) 0%, transparent 70%)",
          }}
        />

        {/* Candlestick icon */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "16px" }}>
          <svg width="56" height="56" viewBox="0 0 40 40" fill="none">
            <rect x="16" y="8" width="8" height="20" rx="1" fill="#00D4AA" opacity="0.9" />
            <line x1="20" y1="4" x2="20" y2="8" stroke="#00D4AA" strokeWidth="2" />
            <line x1="20" y1="28" x2="20" y2="34" stroke="#00D4AA" strokeWidth="2" />
            <rect x="5" y="14" width="4" height="8" rx="1" fill="#00D4AA" opacity="0.4" />
            <rect x="23" y="10" width="4" height="10" rx="1" fill="#FFD700" opacity="0.4" />
          </svg>
        </div>

        {/* Title */}
        <div
          style={{
            fontSize: 72,
            fontWeight: 800,
            background: "linear-gradient(135deg, #00D4AA, #00F5C8)",
            backgroundClip: "text",
            color: "transparent",
            marginBottom: "8px",
            letterSpacing: "-2px",
          }}
        >
          TrendRider
        </div>

        {/* Tagline */}
        <div
          style={{
            fontSize: 28,
            color: "#E6EDF3",
            opacity: 0.8,
            marginBottom: "40px",
            fontWeight: 300,
          }}
        >
          Algorithmic Signals. Verified Results.
        </div>

        {/* Stats row */}
        <div
          style={{
            display: "flex",
            gap: "48px",
            alignItems: "center",
          }}
        >
          {[
            { value: "Live", label: "Verified Stats" },
            { value: "Open", label: "Source Code" },
            { value: "/live", label: "Real Numbers" },
          ].map((stat) => (
            <div
              key={stat.label}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 700,
                  color: "#00D4AA",
                  fontFamily: "monospace",
                }}
              >
                {stat.value}
              </div>
              <div
                style={{
                  fontSize: 14,
                  color: "#8B949E",
                  textTransform: "uppercase",
                  letterSpacing: "2px",
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          style={{
            position: "absolute",
            bottom: "24px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: 14,
            color: "#8B949E",
          }}
        >
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: "#00D4AA",
            }}
          />
          trendrider.net — AI-powered crypto trading signals
        </div>
      </div>
    ),
    { ...size }
  );
}
