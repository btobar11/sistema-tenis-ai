import { HashRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import MatchAnalysis from './pages/MatchAnalysis';
import AntiFomo from './pages/AntiFomo';
import MatchHistory from './pages/MatchHistory';
import PlayerProfile from './pages/PlayerProfile';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/player/:id" element={<PlayerProfile />} />
          <Route path="/match/:id" element={<MatchAnalysis />} />
          <Route path="/anti-fomo" element={<AntiFomo />} />
          <Route path="/history" element={<MatchHistory />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;
