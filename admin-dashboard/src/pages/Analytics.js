import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Clock,
  MessageSquare,
  Activity,
  Target,
  AlertCircle
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import axios from 'axios';
import toast from 'react-hot-toast';

const Analytics = () => {
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      // Mock data - in real app, fetch from Flask API
      const mockAnalytics = {
        overview: {
          totalCalls: 156,
          totalRecordings: 142,
          avgCallDuration: 3.2,
          successRate: 87.5,
          avgConfidence: 82.3,
          totalIntents: 46
        },
        callVolume: [
          { date: '2024-01-09', calls: 12, duration: 45 },
          { date: '2024-01-10', calls: 19, duration: 52 },
          { date: '2024-01-11', calls: 15, duration: 38 },
          { date: '2024-01-12', calls: 22, duration: 61 },
          { date: '2024-01-13', calls: 18, duration: 47 },
          { date: '2024-01-14', calls: 8, duration: 29 },
          { date: '2024-01-15', calls: 5, duration: 23 },
        ],
        intentDistribution: [
          { name: 'Order Status', value: 35, color: '#3B82F6' },
          { name: 'Payment Issues', value: 25, color: '#EF4444' },
          { name: 'Account Help', value: 20, color: '#10B981' },
          { name: 'Product Info', value: 15, color: '#F59E0B' },
          { name: 'Refund Request', value: 5, color: '#8B5CF6' },
        ],
        confidenceTrend: [
          { date: '2024-01-09', avgConfidence: 78 },
          { date: '2024-01-10', avgConfidence: 82 },
          { date: '2024-01-11', avgConfidence: 85 },
          { date: '2024-01-12', avgConfidence: 79 },
          { date: '2024-01-13', avgConfidence: 88 },
          { date: '2024-01-14', avgConfidence: 91 },
          { date: '2024-01-15', avgConfidence: 87 },
        ],
        hourlyDistribution: [
          { hour: '9AM', calls: 8 },
          { hour: '10AM', calls: 12 },
          { hour: '11AM', calls: 15 },
          { hour: '12PM', calls: 18 },
          { hour: '1PM', calls: 22 },
          { hour: '2PM', calls: 19 },
          { hour: '3PM', calls: 16 },
          { hour: '4PM', calls: 14 },
          { hour: '5PM', calls: 11 },
        ],
        topIntents: [
          { intent: 'Order Status', count: 35, successRate: 94.3 },
          { intent: 'Payment Issues', count: 25, successRate: 88.0 },
          { intent: 'Account Help', count: 20, successRate: 92.5 },
          { intent: 'Product Info', count: 15, successRate: 96.7 },
          { intent: 'Refund Request', count: 5, successRate: 80.0 },
        ]
      };
      
      setAnalytics(mockAnalytics);
    } catch (error) {
      toast.error('Failed to load analytics');
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, subtitle, trend }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
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
        {trend && (
          <div className={`text-sm font-medium ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
            <p className="text-gray-600 mt-2">Detailed insights into your Voice AI performance</p>
          </div>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
        <StatCard
          title="Total Calls"
          value={analytics.overview?.totalCalls || 0}
          icon={Activity}
          color="bg-primary-500"
          trend={12}
        />
        <StatCard
          title="Success Rate"
          value={`${analytics.overview?.successRate || 0}%`}
          icon={Target}
          color="bg-success-500"
          trend={5.2}
        />
        <StatCard
          title="Avg Duration"
          value={`${analytics.overview?.avgCallDuration || 0}m`}
          icon={Clock}
          color="bg-warning-500"
          trend={-2.1}
        />
        <StatCard
          title="Avg Confidence"
          value={`${analytics.overview?.avgConfidence || 0}%`}
          icon={TrendingUp}
          color="bg-info-500"
          trend={8.7}
        />
        <StatCard
          title="Recordings"
          value={analytics.overview?.totalRecordings || 0}
          icon={MessageSquare}
          color="bg-purple-500"
          trend={15.3}
        />
        <StatCard
          title="Intents"
          value={analytics.overview?.totalIntents || 0}
          icon={Users}
          color="bg-indigo-500"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Call Volume Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Call Volume Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analytics.callVolume}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="calls" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Intent Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Intent Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics.intentDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analytics.intentDistribution?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Additional Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Confidence Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Confidence Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics.confidenceTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="avgConfidence" stroke="#10B981" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Hourly Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Hourly Call Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.hourlyDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="calls" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Intents Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Top Intents Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Intent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Call Count
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analytics.topIntents?.map((intent, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {intent.intent}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {intent.count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {intent.successRate}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ width: `${intent.successRate}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500">{intent.successRate}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 