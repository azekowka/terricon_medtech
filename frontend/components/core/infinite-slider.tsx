"use client";

import { CSSProperties, ReactNode } from "react";

/**
 * Seamless infinite marquee. Renders its children twice and translates the
 * track by -50% so the loop is continuous. Pure CSS (no motion lib), pauses on
 * hover. API mirrors motion-primitives' InfiniteSlider: { gap, reverse, duration }.
 */
export function InfiniteSlider({
  children,
  gap = 16,
  reverse = false,
  duration = 28,
  className = "",
}: {
  children: ReactNode;
  gap?: number;
  reverse?: boolean;
  duration?: number;
  className?: string;
}) {
  const group: CSSProperties = { gap, marginRight: gap };
  return (
    <div className={`infinite-slider relative overflow-hidden ${className}`}>
      <div
        className="marquee-track flex w-max items-center"
        style={{ animationDuration: `${duration}s`, animationDirection: reverse ? "reverse" : "normal" }}
      >
        <div className="flex shrink-0 items-center" style={group}>
          {children}
        </div>
        <div className="flex shrink-0 items-center" style={group} aria-hidden>
          {children}
        </div>
      </div>
    </div>
  );
}
