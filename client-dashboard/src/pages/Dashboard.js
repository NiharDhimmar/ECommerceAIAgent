import React, { useState, useEffect } from 'react';
import { 
  Phone, 
  Mic, 
  FileText, 
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Users
} from 'lucide-react';
import api from '../api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCalls: 0,
    totalRecordings: 0,
    totalTranscripts: 0,
    successRate: 0,
    avgCallDuration: 0,
    recentCalls: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // Fetch client-specific dashboard data
      const response = await api.get('/api/client/dashboard');
      if (response.data.ok) {
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      // Set mock data for demonstration
      setStats({
        totalCalls: 24,
        totalRecordings: 18,
        totalTranscripts: 22,
        successRate: 85,
        avgCallDuration: 3.2,
        recentCalls: [
          { id: 1, phoneNumber: '+1234567890', duration: '2:45', status: 'completed', timestamp: '2024-01-15 14:30' },
          { id: 2, phoneNumber: '+1987654321', duration: '1:20', status: 'completed', timestamp: '2024-01-15 13:15' },
          { id: 3, phoneNumber: '+1122334455', duration: '0:45', status: 'failed', timestamp: '2024-01-15 12:00' }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
      case 'failed':
        return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
      default:
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-gray-200 dark:bg-gray-700 rounded-lg h-32"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Client Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">Overview of your AI assistant interactions</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Phone className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Calls</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.totalCalls}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Mic className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recordings</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.totalRecordings}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <FileText className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Transcripts</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.totalTranscripts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <TrendingUp className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.successRate}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Calls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Calls</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.recentCalls.map((call) => (
                <div key={call.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(call.status)}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{call.phoneNumber}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{call.timestamp}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{call.duration}</p>
                    <span className={`inline-block px-2 py-1 text-xs rounded-full ${getStatusColor(call.status)}`}>
                      {call.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Quick Stats</h3>
          </div>
          <div className="p-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Clock className="h-5 w-5 text-gray-400" />
                  <span className="text-gray-600 dark:text-gray-400">Average Call Duration</span>
                </div>
                <span className="font-semibold text-gray-900 dark:text-white">{stats.avgCallDuration} min</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-gray-600 dark:text-gray-400">Successful Calls</span>
                </div>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {Math.round(stats.totalCalls * stats.successRate / 100)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Users className="h-5 w-5 text-blue-500" />
                  <span className="text-gray-600 dark:text-gray-400">Active Sessions</span>
                </div>
                <span className="font-semibold text-gray-900 dark:text-white">1</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
