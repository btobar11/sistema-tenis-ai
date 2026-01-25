import { HashRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
// import MatchAnalysis from './pages/MatchAnalysis'; // Unused
import DailyDashboard from './pages/DailyDashboard';
import MatchComparison from './pages/MatchComparison';
import AntiFomo from './pages/AntiFomo';
import MatchHistory from './pages/MatchHistory';
import PlayerProfile from './pages/PlayerProfile';
import PerformancePage from './pages/PerformancePage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<DailyDashboard />} />
          <Route path="/player/:id" element={<PlayerProfile />} />
          <Route path="/match/:idA/:idB" element={<MatchComparison />} />
          {/* Legacy routes kept for reference if needed */}
          <Route path="/anti-fomo" element={<AntiFomo />} />
          <Route path="/journal" element={<Dashboard initialView="journal" />} />
          <Route path="/history" element={<MatchHistory />} />
          <Route path="/performance" element={<PerformancePage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;
