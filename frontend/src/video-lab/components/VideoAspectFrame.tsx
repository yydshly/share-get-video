/**
 * VideoAspectFrame.tsx — V1.2.1.5
 *
 * A wrapper that enforces a specific aspect-ratio on its child <video> element
 * so that vertical (9:16) videos are never cropped when placed in wider
 * containers.  Uses CSS aspect-ratio + object-fit: contain.
 *
 * Default: 9:16, contain — matching the project default output format.
 */

import React from "react";
import { aspectRatioToCss } from "../utils/aspectRatio";

export type { AspectRatio } from "../utils/aspectRatio";

export interface VideoAspectFrameProps {
  /** Normalised aspect ratio string (e.g. "9:16"). Defaults to "9:16". */
  aspectRatio?: string;
  /** How the video fills the container. Defaults to "contain" (no cropping). */
  fitMode?: "contain" | "cover";
  children: React.ReactNode;
  /** Max height of the frame in pixels. Defaults to 320. */
  maxHeight?: number | string;
  /** Extra CSS class */
  className?: string;
}

export function VideoAspectFrame({
  aspectRatio = "9:16",
  fitMode = "contain",
  children,
  maxHeight = 320,
  className,
}: VideoAspectFrameProps) {
  return (
    <div
      className={className}
      style={{
        width: "100%",
        maxHeight,
        aspectRatio: aspectRatioToCss(aspectRatio),
        background: "#020617",
        borderRadius: 12,
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
      data-aspect-ratio={aspectRatio}
      data-fit-mode={fitMode}
    >
      {/* Ensures video fills the aspect-ratio box without distortion */}
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ style?: React.CSSProperties }>, {
            style: {
              ...((child as React.ReactElement<{ style?: React.CSSProperties }>).props?.style || {}),
              width: "100%",
              height: "100%",
              objectFit: fitMode,
            },
          });
        }
        return child;
      })}
    </div>
  );
}
