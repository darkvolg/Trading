export function CandlestickChart() {
  const candles = [
    { x: 20,  open: 130, close: 110, high: 100, low: 145 },
    { x: 50,  open: 112, close:  90, high:  82, low: 125 },
    { x: 80,  open:  92, close: 108, high:  78, low: 115 },
    { x: 110, open: 106, close:  88, high:  80, low: 118 },
    { x: 140, open:  90, close:  72, high:  65, low: 100 },
    { x: 170, open:  74, close:  95, high:  60, low: 102 },
    { x: 200, open:  93, close:  78, high:  70, low: 105 },
    { x: 230, open:  80, close:  60, high:  52, low:  90 },
    { x: 260, open:  62, close:  48, high:  40, low:  72 },
    { x: 290, open:  50, close:  70, high:  38, low:  78 },
    { x: 320, open:  68, close:  52, high:  44, low:  80 },
    { x: 350, open:  54, close:  36, high:  28, low:  62 },
    { x: 380, open:  38, close:  55, high:  25, low:  62 },
    { x: 410, open:  53, close:  40, high:  32, low:  60 },
    { x: 440, open:  42, close:  28, high:  20, low:  50 },
    { x: 470, open:  30, close:  48, high:  18, low:  55 },
    { x: 500, open:  46, close:  62, high:  35, low:  68 },
    { x: 530, open:  60, close:  45, high:  38, low:  70 },
    { x: 560, open:  47, close:  30, high:  22, low:  55 },
    { x: 590, open:  32, close:  50, high:  20, low:  58 },
  ];

  const linePoints = candles.map(c => `${c.x},${Math.min(c.open, c.close)}`).join(" ");

  // Pseudo-random shuffle for glow order (deterministic, SSR-safe)
  const glowOrder = [14, 3, 17, 7, 11, 0, 19, 5, 13, 9, 2, 16, 8, 4, 18, 10, 1, 15, 6, 12];

  return (
    <svg
      className="absolute inset-0 w-full h-full"
      viewBox="0 0 620 200"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      {/* Glow filters */}
      <defs>
        <filter id="glowGreen" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feFlood floodColor="#00D4AA" floodOpacity="0.8" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glowRed" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feFlood floodColor="#FF4757" floodOpacity="0.8" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {/* Trend line */}
      <polyline
        points={linePoints}
        fill="none"
        stroke="#00D4AA"
        strokeWidth="1.5"
        strokeDasharray="1000"
        strokeDashoffset="0"
        opacity="0.07"
        style={{ animation: "chartLine 2s ease-out forwards" }}
      />
      {/* Candles */}
      {candles.map((c, i) => {
        const isGreen = c.close < c.open;
        const color = isGreen ? "#00D4AA" : "#FF4757";
        const filterId = isGreen ? "glowGreen" : "glowRed";
        const bodyTop = Math.min(c.open, c.close);
        const bodyH = Math.abs(c.open - c.close);
        const glowSlot = glowOrder[i] ?? i;
        const glowDelay = glowSlot * 0.5;
        const totalCycle = candles.length * 0.5 + 3;
        return (
          <g
            key={i}
            style={{
              animation: `candleRise 0.5s ease-out ${i * 0.06}s forwards, candleGlowPulse ${totalCycle}s ease-in-out ${glowDelay}s infinite`,
              opacity: 0,
              "--glow-filter": `url(#${filterId})`,
            } as React.CSSProperties}
            className="candle-group"
          >
            {/* Wick */}
            <line x1={c.x} y1={c.high} x2={c.x} y2={c.low} stroke={color} strokeWidth="1" />
            {/* Body */}
            <rect x={c.x - 7} y={bodyTop} width="14" height={Math.max(bodyH, 2)} fill={color} rx="1" />
          </g>
        );
      })}
      {/* Grid lines */}
      {[50, 100, 150].map(y => (
        <line key={y} x1="0" y1={y} x2="620" y2={y} stroke="#00D4AA" strokeWidth="0.5" opacity="0.05" strokeDasharray="4 8" />
      ))}
    </svg>
  );
}
