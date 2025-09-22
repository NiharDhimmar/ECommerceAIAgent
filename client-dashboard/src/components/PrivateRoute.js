import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import api from '../api';

const PrivateRoute = ({ children }) => {
  const location = useLocation();
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const { data } = await api.get('/api/auth/me');
        if (mounted) {
          // Check if user is authenticated (both admin and client users can access client dashboard)
          const isAuthenticated = Boolean(data?.authenticated);
          setAuthed(isAuthenticated);
        }
      } catch (e) {
        if (mounted) setAuthed(false);
      } finally {
        if (mounted) setChecking(false);
      }
    })();
    return () => { mounted = false; };
  }, []); // Remove location.pathname dependency to prevent infinite loops

  if (checking) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400 text-lg">Authenticating...</p>
        </div>
      </div>
    );
  }

  if (!authed) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
};

export default PrivateRoute;
