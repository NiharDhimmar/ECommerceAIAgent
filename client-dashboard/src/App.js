import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Calls from './pages/Calls';
import Recordings from './pages/Recordings';
import Transcripts from './pages/Transcripts';
import Profile from './pages/Profile';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password/:token" element={<ResetPassword />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
                  <Sidebar />
                  <div className="flex-1 flex flex-col min-w-0">
                    <Header />
                    <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900">
                      <div className="max-w-full mx-auto">
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/profile" element={<Profile />} />
                          <Route path="/calls" element={<Calls />} />
                          <Route path="/recordings" element={<Recordings />} />
                          <Route path="/transcripts" element={<Transcripts />} />
                          <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                      </div>
                    </main>
                  </div>
                </div>
              </PrivateRoute>
            }
          />
        </Routes>
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;
