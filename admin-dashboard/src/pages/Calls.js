import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Clock,
  ChevronLeft,
  ChevronRight,
  Phone
} from 'lucide-react';
import api from '../api';
import toast from 'react-hot-toast';

const Calls = () => {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/calls`);
      setCalls(data || []);
    } catch (error) {
      toast.error('Failed to load calls');
      console.error('Error fetching calls:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCalls = calls.filter(call => {
    const matchesSearch = (call.phoneNumber || '').includes(searchTerm) || 
                         (call.id || '').includes(searchTerm) ||
                         (call.fromNumber || '').includes(searchTerm) ||
                         (call.toNumber || '').includes(searchTerm);
    const matchesStatus = statusFilter === 'all' || call.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'in-progress':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Pagination logic
  const totalPages = Math.ceil(filteredCalls.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentItems = filteredCalls.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading calls...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Calls</h1>
        <p className="text-gray-600 mt-2">Manage and monitor all voice calls</p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search by call ID or phonenumbers..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="in-progress">In Progress</option>
            </select>
            <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              <Filter className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Calls Table */}
      {filteredCalls.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="max-h-[70vh] overflow-auto rounded-t-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">From</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">To</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Time</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {currentItems.map((call) => (
                  <tr key={call.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 break-all">{call.id}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{call.fromNumber || ''}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{call.toNumber || ''}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1 text-gray-400 flex-shrink-0" />
                        <span>{call.duration}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(call.status)}`}>
                        {call.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">{call.startTime}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{call.endTime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-gray-500 text-center sm:text-left">
                  Showing {startIndex + 1} to {Math.min(endIndex, filteredCalls.length)} of {filteredCalls.length} calls
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <span className="text-sm text-gray-500 px-2">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {filteredCalls.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Phone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No calls found</h3>
          <p className="text-gray-500">No calls match your current search criteria.</p>
        </div>
      )}
    </div>
  );
};

export default Calls; 