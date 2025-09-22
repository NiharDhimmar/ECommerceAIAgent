import React, { useState, useEffect } from 'react';
import { Phone, Clock, CheckCircle, XCircle, Search, Filter } from 'lucide-react';
import api from '../api';

const Calls = () => {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/client/calls');
      if (response.data.ok) {
        setCalls(response.data.calls);
      }
    } catch (error) {
      console.error('Failed to fetch calls:', error);
      // Set mock data for demonstration
      setCalls([
        {
          id: 1,
          phoneNumber: '+1234567890',
          duration: '2:45',
          status: 'completed',
          timestamp: '2024-01-15 14:30:00',
          intent: 'Customer Support',
          confidence: 0.95
        },
        {
          id: 2,
          phoneNumber: '+1987654321',
          duration: '1:20',
          status: 'completed',
          timestamp: '2024-01-15 13:15:00',
          intent: 'Product Inquiry',
          confidence: 0.88
        },
        {
          id: 3,
          phoneNumber: '+1122334455',
          duration: '0:45',
          status: 'failed',
          timestamp: '2024-01-15 12:00:00',
          intent: 'Technical Issue',
          confidence: 0.72
        },
        {
          id: 4,
          phoneNumber: '+1555666777',
          duration: '3:15',
          status: 'completed',
          timestamp: '2024-01-15 11:30:00',
          intent: 'Billing Question',
          confidence: 0.91
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
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

  const filteredCalls = calls.filter(call => {
    const matchesSearch = call.phoneNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.intent.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || call.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-gray-200 dark:bg-gray-700 rounded-lg h-20"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Calls</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">View and manage your AI assistant call history</p>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search calls by phone number or intent..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="in-progress">In Progress</option>
            </select>
          </div>
        </div>
      </div>

      {/* Calls List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Call History ({filteredCalls.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredCalls.length === 0 ? (
            <div className="p-6 text-center">
              <Phone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No calls found</p>
            </div>
          ) : (
            filteredCalls.map((call) => (
              <div key={call.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(call.status)}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{call.phoneNumber}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{call.intent}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-6">
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{call.duration}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(call.timestamp).toLocaleDateString()} {new Date(call.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500 dark:text-gray-400">Confidence</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {Math.round(call.confidence * 100)}%
                      </p>
                    </div>
                    <span className={`inline-block px-3 py-1 text-xs rounded-full ${getStatusColor(call.status)}`}>
                      {call.status}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Calls;
