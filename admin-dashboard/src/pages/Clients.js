import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import toast from 'react-hot-toast';
import { Search, Users, Filter, Tag, ChevronLeft, ChevronRight, RefreshCw, Plus, Edit2, Trash2, X } from 'lucide-react';

const Clients = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [refreshing, setRefreshing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({ id: null, name: '', phone: '', email: '', company: '', status: 'lead', tags: [] });

  const loadClients = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true); else setLoading(true);
      const params = new URLSearchParams();
      if (searchTerm) params.set('search', searchTerm);
      if (statusFilter !== 'all') params.set('status', statusFilter);
      params.set('page', String(currentPage));
      params.set('pageSize', String(pageSize));
      const { data } = await api.get(`/api/clients?${params.toString()}`);
      const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
      setClients(items);
    } catch (err) {
      console.error('Failed to load clients:', err?.response?.data || err);
      toast.error('Failed to load clients');
      setClients([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadClients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, pageSize]);

  const filtered = useMemo(() => {
    const term = (searchTerm || '').toLowerCase();
    return clients.filter((c) => {
      const inText = `${c.name || ''} ${c.phone || c.phoneNumber || ''} ${c.email || ''} ${c.company || ''}`.toLowerCase();
      const matchesSearch = term ? inText.includes(term) : true;
      const matchesStatus = statusFilter === 'all' || (c.status || '').toLowerCase() === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [clients, searchTerm, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentItems = filtered.slice(startIndex, endIndex);

  const statusBadge = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'lead':
        return 'bg-blue-100 text-blue-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'vip':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const openNewModal = () => {
    setFormData({ id: null, name: '', phone: '', email: '', company: '', status: 'lead', tags: [] });
    setIsModalOpen(true);
  };

  const openEditModal = (client) => {
    setFormData({
      id: client.id,
      name: client.name || '',
      phone: client.phone || client.phoneNumber || '',
      email: client.email || '',
      company: client.company || '',
      status: (client.status || 'lead').toLowerCase(),
      tags: Array.isArray(client.tags) ? client.tags : [],
    });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const payload = {
        name: formData.name.trim(),
        phone: formData.phone.trim(),
        email: formData.email.trim() || undefined,
        company: formData.company.trim() || undefined,
        status: formData.status,
        tags: formData.tags,
      };
      if (!payload.name || !payload.phone) {
        toast.error('Name and phone are required');
        return;
      }
      if (formData.id) {
        await api.put(`/api/clients/${formData.id}`, payload);
        toast.success('Client updated');
      } else {
        await api.post(`/api/clients`, payload);
        toast.success('Client created');
      }
      setIsModalOpen(false);
      await loadClients(true);
    } catch (err) {
      const msg = err?.response?.data?.details || err?.response?.data?.error || err?.message || 'Failed to save client';
      toast.error(msg);
      console.error('Save client error:', err?.response?.data || err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (client) => {
    try {
      const proceed = window.confirm(`Delete client ${client.name || client.phone || client.email || client.id}?`);
      if (!proceed) return;
      await api.delete(`/api/clients/${client.id}`);
      toast.success('Client deleted');
      await loadClients(true);
    } catch (err) {
      const msg = err?.response?.data?.details || err?.response?.data?.error || err?.message || 'Failed to delete client';
      toast.error(msg);
      console.error('Delete client error:', err?.response?.data || err);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Clients</h1>
            <p className="text-gray-600 mt-2">Manage your customers and view their interactions</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadClients(true)}
              disabled={refreshing || loading}
              className="inline-flex items-center px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={openNewModal}
              className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <Plus className="h-4 w-4 mr-2" /> New Client
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4 md:p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search by name, phone, or email..."
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
              <option value="lead">Lead</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="vip">VIP</option>
            </select>
            <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              <Filter className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center">
          <Users className="h-5 w-5 text-primary-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Client List ({filtered.length})</h3>
          <div className="ml-auto flex items-center space-x-2">
            <span className="text-sm text-gray-500">Show:</span>
            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>

        <div className="max-h-[70vh] overflow-auto rounded-t-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Contact</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {currentItems.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    <Link to={`/clients/${c.id}`} className="text-primary-600 hover:text-primary-700 hover:underline">
                      {c.name || '—'}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{c.phone || c.phoneNumber || '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{c.email || '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{c.company || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusBadge(c.status)}`}>
                      {c.status || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    <div className="flex flex-wrap gap-1">
                      {(c.tags || []).slice(0, 3).map((t, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-800 text-xs">
                          <Tag className="h-3 w-3 mr-1" /> {t}
                        </span>
                      ))}
                      {(Array.isArray(c.tags) && c.tags.length > 3) && (
                        <span className="text-xs text-gray-500">+{c.tags.length - 3} more</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{c.lastContactAt || c.last_contact_at || '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <Link to={`/clients/${c.id}`} className="text-primary-600 hover:text-primary-700">View</Link>
                      <button onClick={() => openEditModal(c)} className="inline-flex items-center text-gray-600 hover:text-gray-800">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(c)} className="inline-flex items-center text-red-600 hover:text-red-700">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {currentItems.length === 0 && !loading && (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                    No clients found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 md:px-6 py-4 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-sm text-gray-500 text-center sm:text-left">
                Showing {filtered.length === 0 ? 0 : startIndex + 1} to {Math.min(endIndex, filtered.length)} of {filtered.length} clients
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 hover:bg-gray-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-500 px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 hover:bg-gray-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">{formData.id ? 'Edit Client' : 'New Client'}</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="+1..."
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="name@company.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Company Inc"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="lead">Lead</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="vip">VIP</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma separated)</label>
                  <input
                    type="text"
                    value={formData.tags.join(', ')}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="vip, wholesale"
                  />
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
              <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
              <button onClick={handleSave} disabled={saving} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
                {saving ? 'Saving...' : (formData.id ? 'Save Changes' : 'Create Client')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Clients;
