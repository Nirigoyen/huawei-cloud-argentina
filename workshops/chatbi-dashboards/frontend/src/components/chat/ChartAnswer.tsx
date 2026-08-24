"use client";

import { useEffect, useRef } from "react";
import type { Result, VisualizationSpec } from "vega-embed";
import type { ChartSpec } from "@/lib/api";

// Dark theme config for Vega-Lite charts so axes/labels read on a dark bg.
const DARK_CONFIG = {
  background: "transparent",
  view: { stroke: null },
  axis: {
    labelColor: "#cbd5e1",
    titleColor: "#e2e8f0",
    gridColor: "#1e293b",
    domainColor: "#475569",
    tickColor: "#475569",
  },
  axisX: { labelColor: "#cbd5e1", titleColor: "#e2e8f0" },
  axisY: { labelColor: "#cbd5e1", titleColor: "#e2e8f0" },
  legend: {
    labelColor: "#cbd5e1",
    titleColor: "#e2e8f0",
    symbolStroke: "#cbd5e1",
  },
  title: { color: "#f1f5f9", subtitleColor: "#94a3b8" },
  header: { labelColor: "#cbd5e1" },
  mark: { color: "#6366f1" },
};

/**
 * Render a Vega-Lite chart.
 * - `fill` (dashboard): chart absolutely fills its positioned parent and redraws on resize.
 * - no `fill` (chat): chart is responsive in width, fixed height (spec or 280px).
 */
export function ChartAnswer({ spec, fill }: { spec: ChartSpec; fill?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let view: Result | undefined;
    let ro: ResizeObserver | null = null;
    let resizeTimer: ReturnType<typeof setTimeout> | null = null;

    (async () => {
      try {
        const embed = (await import("vega-embed")).default;
        if (!ref.current || !spec) return;

        const responsiveSpec = {
          ...spec,
          width: "container",
          height: fill ? "container" : (spec.height ?? 280),
        } as unknown as VisualizationSpec;
        view = await embed(ref.current, responsiveSpec, {
          actions: false,
          renderer: "svg",
          config: DARK_CONFIG,
        });

        // Redraw when the container is resized (e.g. dashboard drag-resize).
        // vega-embed has its own observer for "container", but react-grid-layout
        // resize doesn't always trigger it, so we force a resize+run explicitly.
        if (fill && ref.current) {
          ro = new ResizeObserver(() => {
            if (resizeTimer) clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
              try {
                view?.view.resize().run();
              } catch {
                /* ignore */
              }
            }, 80);
          });
          ro.observe(ref.current);
        }
      } catch {
        /* ignore render errors */
      }
    })();

    return () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      ro?.disconnect();
      try {
        view?.finalize();
      } catch {
        /* ignore */
      }
    };
  }, [spec, fill]);

  // `absolute inset-0` gives definite pixel dimensions from a `relative` parent,
  // which Vega-Lite's "container" sizing needs (especially for height).
  return <div ref={ref} className={fill ? "absolute inset-0" : "w-full"} />;
}
