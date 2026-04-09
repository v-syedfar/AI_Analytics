import React, { useState, useRef, useEffect } from "react";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
}

/**
 * Reusable tooltip wrapper.
 * Desktop: shows on hover. Touch: shows on tap of ⓘ icon.
 * Content must be data-driven — never pass hardcoded placeholder text.
 */
export const Tooltip: React.FC<TooltipProps> = ({ content, children }) => {
  const [visible, setVisible] = useState(false);
  const [isTouch, setIsTouch] = useState(false);
  const [flipUp, setFlipUp] = useState(true);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = () => setIsTouch(true);
    window.addEventListener("touchstart", handler, { once: true });
    return () => window.removeEventListener("touchstart", handler);
  }, []);

  useEffect(() => {
    if (visible && wrapperRef.current && tooltipRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect();
      const tooltipHeight = tooltipRef.current.offsetHeight;
      setFlipUp(rect.top > tooltipHeight + 16);
    }
  }, [visible]);

  // Close on outside click (touch mode)
  useEffect(() => {
    if (!isTouch || !visible) return;
    const handler = (e: MouseEvent | TouchEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setVisible(false);
      }
    };
    document.addEventListener("mousedown", handler);
    document.addEventListener("touchstart", handler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("touchstart", handler);
    };
  }, [isTouch, visible]);

  return (
    <div
      ref={wrapperRef}
      className="relative inline-block w-full"
      onMouseEnter={() => !isTouch && setVisible(true)}
      onMouseLeave={() => !isTouch && setVisible(false)}
    >
      {children}

      {/* Touch info icon */}
      {isTouch && (
        <button
          onClick={() => setVisible((v) => !v)}
          className="absolute top-2 right-2 text-gray-400 hover:text-blue-400 text-xs leading-none z-10"
          aria-label="Show tooltip"
        >
          ⓘ
        </button>
      )}

      {/* Tooltip panel */}
      <div
        ref={tooltipRef}
        className={`
          absolute z-50 max-w-xs w-72 p-3 rounded-lg text-xs
          bg-[#161b22] border border-white/10 text-[#e6edf3]
          shadow-xl pointer-events-none
          transition-all duration-200
          ${flipUp ? "bottom-full mb-2" : "top-full mt-2"}
          left-0
          ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1"}
        `}
        style={{ transitionProperty: "opacity, transform" }}
      >
        {content}
      </div>
    </div>
  );
};

/** Helper to safely display a value or "N/A" */
export function val(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === "") return "N/A";
  return String(v);
}
