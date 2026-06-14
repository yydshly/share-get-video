// Root.tsx - Remotion entry point
// V0.3.1.1: Standard Composition pattern

import React from "react";
import { Composition, registerRoot } from "remotion";
import { AiNewsVideo } from "./AiNewsVideo";
import { defaultProps } from "./data";

const fps = 30;
const durationInFrames = Math.max(450, Math.ceil((defaultProps.durationSec || 45) * fps));

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AiNewsVideo"
        component={AiNewsVideo}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
    </>
  );
};

registerRoot(RemotionRoot);

export { defaultProps };
