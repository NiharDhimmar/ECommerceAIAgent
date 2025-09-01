import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Calls from './pages/Calls';
import Recordings from './pages/Recordings';
import Transcripts from './pages/Transcripts';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Numbers from './pages/Numbers';

function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/calls" element={<Calls />} />
              <Route path="/recordings" element={<Recordings />} />
              <Route path="/transcripts" element={<Transcripts />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/numbers" element={<Numbers />} />
            </Routes>
          </main>
        </div>
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App; 