import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Lock, User } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      const { data } = await api.post('/api/auth/login', { username, password });
      if (data?.ok) {
        toast.success('Logged in');
        navigate(from, { replace: true });
      } else {
        const msg = data?.error || 'Invalid credentials';
        setError(msg);
        toast.error(msg);
      }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Login failed';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100">
      {/* Desktop Layout */}
      <div className="hidden lg:flex min-h-screen">
        {/* Left Side - Branding/Info */}
        <div className="flex-1 flex flex-col justify-center items-center bg-gradient-to-br from-primary-600 to-primary-800 text-white p-12">
          <div className="max-w-md text-center">
            <div className="inline-flex items-center justify-center h-20 w-20 rounded-3xl bg-white/20 backdrop-blur-sm shadow-2xl mb-8">
              <Lock className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl font-extrabold mb-4 tracking-tight">AgentAI Operations Dashboard</h1>
            <h2 className="text-2xl font-semibold mb-6">Admin Dashboard</h2>
            <p className="text-lg text-primary-100 leading-relaxed">
              Manage your voice AI system with comprehensive analytics, call monitoring, and intelligent insights.
            </p>
            <div className="mt-8 grid grid-cols-2 gap-6 text-sm">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span>Real-time Analytics</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span>Call Management</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span>Smart Recordings</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span>AI Insights</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right Side - Login Form */}
        <div className="flex-1 flex items-center justify-center p-12">
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-primary-600 shadow-lg shadow-primary-200 mb-6">
                <Lock className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Welcome back</h1>
              <p className="mt-2 text-gray-600">Sign in to access your admin dashboard</p>
            </div>
            <div className="bg-white/95 backdrop-blur-sm p-8 rounded-2xl shadow-xl ring-1 ring-gray-100">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Username</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition"
                      placeholder="admin"
                      autoFocus
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-3 border border-gray-300 rounded-xl focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition"
                    placeholder="••••••••"
                  />
                </div>
                {error && (
                  <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</div>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 shadow-lg shadow-primary-200 transition font-semibold"
                >
                  {loading ? 'Signing in...' : 'Sign in'}
                </button>
              </form>
              <div className="mt-6 text-center">
                <Link
                  to="/forgot-password"
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Forgot your password?
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile/Tablet Layout */}
      <div className="lg:hidden flex items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary-600 shadow-lg shadow-primary-200">
            <Lock className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-4 text-3xl font-extrabold text-gray-900 tracking-tight">Welcome back</h1>
          <p className="mt-1 text-gray-600">Sign in to access your admin dashboard</p>
        </div>
        <div className="bg-white/90 backdrop-blur-sm p-8 rounded-2xl shadow-xl ring-1 ring-gray-100">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-xl focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition"
                  placeholder="admin"
                  autoFocus
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition"
                placeholder="••••••••"
              />
            </div>
            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 shadow-lg shadow-primary-200 transition"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
            <div className="mt-6 text-center">
              <Link
                to="/forgot-password"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                Forgot your password?
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
