// Frontend App with React Router

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import VideoLabHome from "./video-lab/pages/VideoLabHome";
import VideoTestCasesPage from "./video-lab/pages/VideoTestCasesPage";
import VideoMethodsPage from "./video-lab/pages/VideoMethodsPage";
import VideoExperimentPage from "./video-lab/pages/VideoExperimentPage";
import VideoExperimentDetailPage from "./video-lab/pages/VideoExperimentDetailPage";
import VideoComparePage from "./video-lab/pages/VideoComparePage";
import VideoAdvicePage from "./video-lab/pages/VideoAdvicePage";
import RouteBenchmarkPage from "./video-lab/pages/RouteBenchmarkPage";
import RoutePlaygroundPage from "./video-lab/pages/RoutePlaygroundPage";
import VisualComposePage from "./video-lab/pages/VisualComposePage";
import FramePreviewPage from "./video-lab/pages/FramePreviewPage";
import QualityHistoryPage from "./video-lab/pages/QualityHistoryPage";
import StyleGalleryPage from "./video-lab/pages/StyleGalleryPage";
import RouteBaselineComparisonPage from "./video-lab/pages/RouteBaselineComparisonPage";
import RemotionStyleFamilyPage from "./video-lab/pages/RemotionStyleFamilyPage";
import VideoGenerationWorkbenchPage from "./video-lab/pages/VideoGenerationWorkbenchPage";
import TechniqueProbePage from "./video-lab/pages/TechniqueProbePage";
import StyleSweepPage from "./video-lab/pages/StyleSweepPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/video-lab" element={<VideoLabHome />} />
        <Route path="/video-lab/test-cases" element={<VideoTestCasesPage />} />
        <Route path="/video-lab/methods" element={<VideoMethodsPage />} />
        <Route path="/video-lab/experiments/new" element={<VideoExperimentPage />} />
        <Route path="/video-lab/experiments/:id" element={<VideoExperimentDetailPage />} />
        <Route path="/video-lab/compare" element={<VideoComparePage />} />
        <Route path="/video-lab/advice" element={<VideoAdvicePage />} />
        <Route path="/video-lab/route-benchmark" element={<RouteBenchmarkPage />} />
        <Route path="/video-lab/route-playground" element={<RoutePlaygroundPage />} />
        <Route path="/video-lab/visual-compose" element={<VisualComposePage />} />
        <Route path="/video-lab/frame-preview" element={<FramePreviewPage />} />
        <Route path="/video-lab/quality-history" element={<QualityHistoryPage />} />
        <Route path="/video-lab/style-gallery" element={<StyleGalleryPage />} />
        <Route path="/video-lab/route-baseline-comparison" element={<RouteBaselineComparisonPage />} />
        <Route path="/video-lab/remotion-style-family" element={<RemotionStyleFamilyPage />} />
        <Route path="/video-lab/workbench" element={<VideoGenerationWorkbenchPage />} />
        <Route path="/video-lab/technique-probe" element={<TechniqueProbePage />} />
        <Route path="/video-lab/style-sweep" element={<StyleSweepPage />} />
        <Route path="/" element={<Navigate to="/video-lab" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
