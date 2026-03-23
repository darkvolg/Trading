import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "404 — Page Not Found | TrendRider",
};

export default function NotFound() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#0D1117",
        color: "#E6EDF3",
        fontFamily: "var(--font-inter), sans-serif",
        textAlign: "center",
        padding: "2rem",
      }}
    >
      <h1
        style={{
          fontSize: "clamp(6rem, 15vw, 12rem)",
          fontWeight: 800,
          lineHeight: 1,
          margin: 0,
          background: "linear-gradient(135deg, #00D4AA 0%, #00A88A 50%, #007766 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          fontFamily: "var(--font-jetbrains), monospace",
        }}
      >
        404
      </h1>

      <h2
        style={{
          fontSize: "1.5rem",
          fontWeight: 600,
          margin: "1.5rem 0 0.75rem",
          color: "#E6EDF3",
        }}
      >
        Page Not Found
      </h2>

      <p
        style={{
          fontSize: "1rem",
          color: "#8B949E",
          maxWidth: "28rem",
          margin: "0 0 2.5rem",
          lineHeight: 1.6,
        }}
      >
        This page doesn&apos;t exist or has been moved.
      </p>

      <Link
        href="/"
        style={{
          display: "inline-block",
          padding: "0.75rem 2rem",
          backgroundColor: "#00D4AA",
          color: "#0D1117",
          fontWeight: 600,
          fontSize: "0.95rem",
          borderRadius: "0.5rem",
          textDecoration: "none",
          transition: "opacity 0.2s",
        }}
      >
        Back to Home
      </Link>
    </div>
  );
}
