import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail, Lock } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      const { data } = await api.post('/api/auth/forgot-password', { email });
      if (data?.ok) {
        setSuccess(true);
        toast.success('Password reset instructions sent to your email');
      } else {
        const msg = data?.error || 'Failed to send reset instructions';
        setError(msg);
        toast.error(msg);
      }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Failed to send reset instructions';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-green-600 shadow-lg shadow-green-200 mb-6">
              <Mail className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Check Your Email</h1>
            <p className="mt-2 text-gray-600">We've sent password reset instructions to your email address</p>
          </div>
          <div className="bg-white/95 backdrop-blur-sm p-8 rounded-2xl shadow-xl ring-1 ring-gray-100">
            <div className="text-center space-y-4">
              <p className="text-gray-600">
                If you don't see the email in your inbox, please check your spam folder.
              </p>
              <p className="text-sm text-gray-500">
                The reset link will expire in 1 hour for security reasons.
              </p>
              <div className="pt-4">
                <Link
                  to="/login"
                  className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Login
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-primary-600 shadow-lg shadow-primary-200 mb-6">
            <Lock className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Forgot Password?</h1>
          <p className="mt-2 text-gray-600">Enter your email address and we'll send you reset instructions</p>
        </div>
        <div className="bg-white/95 backdrop-blur-sm p-8 rounded-2xl shadow-xl ring-1 ring-gray-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition"
                  placeholder="Enter your email"
                  required
                  autoFocus
                />
              </div>
            </div>
            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 shadow-lg shadow-primary-200 transition font-semibold"
            >
              {loading ? 'Sending...' : 'Send Reset Instructions'}
            </button>
          </form>
          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
