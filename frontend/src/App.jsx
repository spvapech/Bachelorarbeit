import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { SpeedInsights } from "@vercel/speed-insights/react"
import Welcome from "./pages/Welcome"
import Dashboard from "./pages/Dashboard"
import ComparePage from "./pages/Compare"
import Finance from "./pages/Finance"

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/welcome" replace />} />
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/finance" element={<Finance />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      
      </Routes>
      <SpeedInsights />
    </Router>
  )
}
