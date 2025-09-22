import React, { useState, useEffect } from 'react';
import { 
  Phone, 
  Mic, 
  FileText, 
  TrendingUp, 
  Clock, 
  Users
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCalls: 0,
    totalRecordings: 0,
    totalTranscripts: 0,
    avgCallDuration: 0,
    successRate: 0,
    activeAgents: 0
  });

  const [recentCalls, setRecentCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Mock data for charts
  const callData = [
    { name: 'Mon', calls: 12, duration: 45 },
    { name: 'Tue', calls: 19, duration: 52 },
    { name: 'Wed', calls: 15, duration: 38 },
    { name: 'Thu', calls: 22, duration: 61 },
    { name: 'Fri', calls: 18, duration: 47 },
    { name: 'Sat', calls: 8, duration: 29 },
    { name: 'Sun', calls: 5, duration: 23 },
  ];

  const intentData = [
    { name: 'Order Status', value: 35, color: '#3B82F6' },
    { name: 'Payment Issues', value: 25, color: '#EF4444' },
    { name: 'Account Help', value: 20, color: '#10B981' },
    { name: 'Product Info', value: 15, color: '#F59E0B' },
    { name: 'Other', value: 5, color: '#8B5CF6' },
  ];

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      // Fetch dashboard stats and recent calls in parallel
      const [statsResponse, callsResponse] = await Promise.all([
        api.get(`/api/dashboard/stats`),
        api.get(`/api/calls?limit=4`)
      ]);
      
      const statsData = statsResponse.data;
      const callsData = callsResponse.data;
      
      // Transform API data to match the expected format
      const recentCallsData = (callsData || []).map(call => ({
        id: call.id,
        phoneNumber: call.phoneNumber || call.fromNumber || '',
        duration: call.duration || '0:00',
        status: call.status || 'completed',
        timestamp: call.startTime || call.endTime || ''
      }));

      setStats(statsData);
      setRecentCalls(recentCallsData);
      setLastUpdated(new Date());
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Overview of your Voice AI system</p>
      </div>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
        <StatCard
          title="Total Calls"
          value={stats.totalCalls}
          icon={Phone}
          color="bg-primary-500"
        />
        <StatCard
          title="Recordings"
          value={stats.totalRecordings}
          icon={Mic}
          color="bg-success-500"
        />
        <StatCard
          title="Transcripts"
          value={stats.totalTranscripts}
          icon={FileText}
          color="bg-warning-500"
        />
        <StatCard
          title="Avg Duration"
          value={`${stats.avgCallDuration}m`}
          icon={Clock}
          color="bg-blue-500"
        />
        <StatCard
          title="Success Rate"
          value={`${stats.successRate}%`}
          icon={TrendingUp}
          color="bg-success-500"
        />
        <StatCard
          title="Active Agents"
          value={stats.activeAgents}
          icon={Users}
          color="bg-primary-500"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Call Volume Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Call Volume (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={callData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="calls" stroke="#3B82F6" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
            </div>

        {/* Intent Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Intent Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={intentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {intentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
          </div>

      {/* Recent Calls */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Recent Calls</h3>
                {lastUpdated && (
                  <p className="text-sm text-gray-500 mt-1">
                    Last updated: {lastUpdated.toLocaleTimeString()}
                  </p>
                )}
              </div>
              <button
                onClick={() => fetchDashboardData(true)}
                disabled={refreshing}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center px-4 py-2 rounded-lg hover:bg-primary-50 transition-colors"
              >
                {refreshing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                    Refreshing...
                  </>
                ) : (
                  'Refresh'
                )}
              </button>
            </div>
        <div className="max-h-[70vh] overflow-auto rounded-t-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Call ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {recentCalls.length > 0 ? (
                recentCalls.map((call) => (
                  <tr key={call.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {call.id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {call.phoneNumber}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {call.duration}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        call.status === 'completed' ? 'bg-green-100 text-green-800' :
                        call.status === 'failed' ? 'bg-red-100 text-red-800' :
                        call.status === 'in-progress' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {call.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {call.timestamp}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <Phone className="h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-lg font-medium">No recent calls found</p>
                      <p className="text-sm mt-1">Calls will appear here once they are made</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {recentCalls.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <a
              href="/calls"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View All Calls →
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 