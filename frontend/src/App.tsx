import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { OverviewPage } from "./pages/OverviewPage";
import { EventsPage } from "./pages/EventsPage";
import { RisksPage } from "./pages/RisksPage";
import { ForecastsPage } from "./pages/ForecastsPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { WhatIfPage } from "./pages/WhatIfPage";
import { LineagePage } from "./pages/LineagePage";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/risks" element={<RisksPage />} />
          <Route path="/forecasts" element={<ForecastsPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/what-if" element={<WhatIfPage />} />
          <Route path="/lineage" element={<LineagePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
