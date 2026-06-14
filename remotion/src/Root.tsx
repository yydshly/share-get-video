// Root.tsx - Remotion entry point
// V0.3.1.1: Standard Composition pattern

import React from "react";
import { Composition, registerRoot } from "remotion";
import { AiNewsVideo } from "./AiNewsVideo";
import { defaultProps } from "./data";
import type { AiNewsVideoProps } from "./data";

const fps = 30;

// 由 props 动态计算合成时长：优先用每段时长之和（与旁白对齐），否则用 durationSec
const computeDurationInFrames = (props: AiNewsVideoProps): number => {
  const sd = props.segmentDurations;
  let totalSec: number;
  if (sd && Array.isArray(sd.cardSecs) && sd.cardSecs.length > 0) {
    totalSec = sd.coverSec + sd.cardSecs.reduce((a, b) => a + b, 0) + sd.summarySec;
  } else {
    totalSec = props.durationSec || 45;
  }
  return Math.max(150, Math.ceil(totalSec * fps));
};

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AiNewsVideo"
        component={AiNewsVideo}
        durationInFrames={computeDurationInFrames(defaultProps)}
        fps={fps}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
        calculateMetadata={({ props }) => ({
          durationInFrames: computeDurationInFrames(props as AiNewsVideoProps),
        })}
      />
    </>
  );
};

registerRoot(RemotionRoot);

export { defaultProps };
