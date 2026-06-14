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
        <Route path="/" element={<Navigate to="/video-lab" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
