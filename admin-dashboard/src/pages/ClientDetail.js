import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import toast from 'react-hot-toast';
import { User, Phone, Mail, Building2, Tag, ArrowLeft, PhoneCall, MessageSquare, Edit2 } from 'lucide-react';

const TabButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium border-b-2 ${active ? 'border-primary-600 text-primary-700' : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'}`}
  >
    {children}
  </button>
);

const ClientDetail = () => {
  const { id } = useParams();

  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');

  const [calls, setCalls] = useState([]);
  const [recordings, setRecordings] = useState([]);
  const [transcripts, setTranscripts] = useState([]);

  const load = async () => {
    try {
      setLoading(true);
      const [{ data: c }, { data: callsData }, { data: recData }, { data: trData }] = await Promise.all([
        api.get(`/api/clients/${id}`),
        api.get(`/api/clients/${id}/calls?limit=10`),
        api.get(`/api/clients/${id}/recordings?limit=10`),
        api.get(`/api/clients/${id}/transcripts?limit=10`),
      ]);
      setClient(c);
      setCalls(Array.isArray(callsData?.items) ? callsData.items : callsData || []);
      setRecordings(Array.isArray(recData?.items) ? recData.items : recData || []);
      setTranscripts(Array.isArray(trData?.items) ? trData.items : trData || []);
    } catch (err) {
      console.error('Failed to load client detail:', err?.response?.data || err);
      toast.error('Failed to load client');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading client details...</p>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="p-6">
        <Link to="/clients" className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-4">
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Clients
        </Link>
        <div className="text-gray-600">Client not found.</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link to="/clients" className="inline-flex items-center text-primary-600 hover:text-primary-700 mr-4">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{client.name || '—'}</h1>
            <p className="text-gray-600 mt-1">Client Profile</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center px-3 py-2 border rounded hover:bg-gray-50">
            <PhoneCall className="h-4 w-4 mr-2" /> Call
          </button>
          <button className="inline-flex items-center px-3 py-2 border rounded hover:bg-gray-50">
            <MessageSquare className="h-4 w-4 mr-2" /> Message
          </button>
          <button className="inline-flex items-center px-3 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">
            <Edit2 className="h-4 w-4 mr-2" /> Edit
          </button>
        </div>
      </div>

      {/* Header Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center">
            <User className="h-5 w-5 text-primary-600 mr-2" />
            <div>
              <div className="text-xs text-gray-500">Name</div>
              <div className="text-sm text-gray-900">{client.name || '—'}</div>
            </div>
          </div>
          <div className="flex items-center">
            <Phone className="h-5 w-5 text-primary-600 mr-2" />
            <div>
              <div className="text-xs text-gray-500">Phone</div>
              <div className="text-sm text-gray-900">{client.phone || client.phoneNumber || '—'}</div>
            </div>
          </div>
          <div className="flex items-center">
            <Mail className="h-5 w-5 text-primary-600 mr-2" />
            <div>
              <div className="text-xs text-gray-500">Email</div>
              <div className="text-sm text-gray-900">{client.email || '—'}</div>
            </div>
          </div>
          <div className="flex items-center">
            <Building2 className="h-5 w-5 text-primary-600 mr-2" />
            <div>
              <div className="text-xs text-gray-500">Company</div>
              <div className="text-sm text-gray-900">{client.company || '—'}</div>
            </div>
          </div>
        </div>
        <div className="mt-4 flex items-center flex-wrap gap-2">
          {(client.tags || []).map((t, i) => (
            <span key={i} className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-800 text-xs">
              <Tag className="h-3 w-3 mr-1" /> {t}
            </span>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-2">
          {['overview','calls','transcripts','recordings','notes'].map((t) => (
            <TabButton key={t} active={tab === t} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </TabButton>
          ))}
        </nav>
      </div>

      {/* Content */}
      {tab === 'overview' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="text-gray-600 text-sm">Last contact: {client.lastContactAt || client.last_contact_at || '—'}</div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Calls</h4>
              <ul className="text-sm text-gray-700 list-disc ml-5">
                {calls.slice(0, 5).map((c) => (
                  <li key={c.id} className="mb-1">
                    {c.startTime || c.timestamp || '—'} · {c.fromNumber || ''} → {c.toNumber || ''} · {c.status || ''}
                  </li>
                ))}
                {calls.length === 0 && <li className="list-none text-gray-500">No calls</li>}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Transcripts</h4>
              <ul className="text-sm text-gray-700 list-disc ml-5">
                {transcripts.slice(0, 5).map((t) => (
                  <li key={t.id} className="mb-1">
                    {t.timestamp || '—'} · messages: {Array.isArray(t.conversation) ? t.conversation.length : 0}
                  </li>
                ))}
                {transcripts.length === 0 && <li className="list-none text-gray-500">No transcripts</li>}
              </ul>
            </div>
          </div>
        </div>
      )}

      {tab === 'calls' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Calls</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">From</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">To</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {calls.map((c) => (
                  <tr key={c.id}>
                    <td className="px-4 py-2 text-sm text-gray-900 break-all">{c.id}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{c.fromNumber || ''}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{c.toNumber || ''}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{c.duration || ''}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{c.status || ''}</td>
                  </tr>
                ))}
                {calls.length === 0 && (
                  <tr><td colSpan="5" className="px-4 py-6 text-center text-gray-500">No calls</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'transcripts' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Transcripts</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Messages</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {transcripts.map((t) => (
                  <tr key={t.id}>
                    <td className="px-4 py-2 text-sm text-gray-900 break-all">{t.callId}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{t.timestamp}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{Array.isArray(t.conversation) ? t.conversation.length : 0}</td>
                  </tr>
                ))}
                {transcripts.length === 0 && (
                  <tr><td colSpan="3" className="px-4 py-6 text-center text-gray-500">No transcripts</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'recordings' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recordings</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">From</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">To</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {recordings.map((r) => (
                  <tr key={r.id}>
                    <td className="px-4 py-2 text-sm text-gray-900 break-all">{r.callId}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{r.fromNumber || ''}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{r.toNumber || ''}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{r.timestamp || ''}</td>
                  </tr>
                ))}
                {recordings.length === 0 && (
                  <tr><td colSpan="4" className="px-4 py-6 text-center text-gray-500">No recordings</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'notes' && (
        <div className="text-gray-500">Notes UI not implemented yet.</div>
      )}
    </div>
  );
};

export default ClientDetail;
