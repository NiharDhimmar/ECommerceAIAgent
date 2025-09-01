import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Search, ShoppingCart, RefreshCw, Globe, Phone, Trash2, ListChecks, Link2 } from 'lucide-react';

const Numbers = () => {
  const [country, setCountry] = useState('US');
  const [numberType, setNumberType] = useState('local');
  const [contains, setContains] = useState('');
  const [areaCode, setAreaCode] = useState('');
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [smsEnabled, setSmsEnabled] = useState(false);
  const [mmsEnabled, setMmsEnabled] = useState(false);
  const [limit, setLimit] = useState(20);

  const [searching, setSearching] = useState(false);
  const [purchasing, setPurchasing] = useState(null); // phoneNumber currently purchasing
  const [available, setAvailable] = useState([]);
  const [owned, setOwned] = useState([]);
  const [loadingOwned, setLoadingOwned] = useState(false);
  const [defaultVoiceUrl, setDefaultVoiceUrl] = useState('');
  const [voiceUrlByNumber, setVoiceUrlByNumber] = useState({});

  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    params.set('country', country);
    params.set('type', numberType);
    if (contains) params.set('contains', contains);
    if (areaCode && numberType === 'local') params.set('area_code', areaCode);
    if (voiceEnabled) params.set('voice_enabled', 'true');
    if (smsEnabled) params.set('sms_enabled', 'true');
    if (mmsEnabled) params.set('mms_enabled', 'true');
    params.set('limit', String(limit));
    return params.toString();
  }, [country, numberType, contains, areaCode, voiceEnabled, smsEnabled, mmsEnabled, limit]);

  const apiBases = ['', 'http://localhost:5000'];

  const getWithFallback = async (path) => {
    let lastErr = null;
    for (const base of apiBases) {
      try {
        const { data } = await axios.get(`${base}${path}`);
        return data;
      } catch (err) {
        lastErr = err;
      }
    }
    throw lastErr;
  };

  const postWithFallback = async (path, body) => {
    let lastErr = null;
    for (const base of apiBases) {
      try {
        const { data } = await axios.post(`${base}${path}`, body);
        return data;
      } catch (err) {
        lastErr = err;
      }
    }
    throw lastErr;
  };

  const deleteWithFallback = async (path) => {
    let lastErr = null;
    for (const base of apiBases) {
      try {
        const { data } = await axios.delete(`${base}${path}`);
        return data;
      } catch (err) {
        lastErr = err;
      }
    }
    throw lastErr;
  };

  const search = async () => {
    try {
      setSearching(true);
      const data = await getWithFallback(`/api/twilio/available-numbers?${queryParams}`);
      setAvailable(data.numbers || []);
      toast.success(`Found ${data.count || (data.numbers || []).length} numbers`);
    } catch (err) {
      const msg = err?.response?.data?.details || err?.response?.data?.error || err?.message || 'Failed to search numbers';
      toast.error(msg);
      console.error('Search numbers error:', err?.response?.data || err);
    } finally {
      setSearching(false);
    }
  };

  const loadOwned = async () => {
    try {
      setLoadingOwned(true);
      const data = await getWithFallback('/api/twilio/my-numbers');
      setOwned(data.numbers || []);
    } catch (err) {
      const msg = err?.response?.data?.details || err?.response?.data?.error || 'Failed to load owned numbers';
      toast.error(msg);
      console.error('Load owned numbers error:', err?.response?.data || err);
    } finally {
      setLoadingOwned(false);
    }
  };

  useEffect(() => {
    loadOwned();
    // Load defaults from settings for nice placeholder (NGROK_URL/voice)
    (async () => {
      try {
        const settings = await getWithFallback('/api/settings');
        const ngrok = settings?.twilio?.ngrokUrl || '';
        if (ngrok) setDefaultVoiceUrl(`${ngrok.replace(/\/$/, '')}/voice`);
      } catch (e) {
        // ignore
      }
    })();
  }, []);

  const purchase = async (phoneNumber) => {
    try {
      setPurchasing(phoneNumber);
      const maybeUrl = (voiceUrlByNumber[phoneNumber] || '').trim();
      const payload = {
        phoneNumber,
        friendlyName: 'VoiceAI Number',
      };
      if (maybeUrl) {
        payload.voiceUrl = maybeUrl;
        payload.voiceMethod = 'POST';
      }
      const confirmMsg = `Do you want to purchase ${phoneNumber} ${payload.voiceUrl ? `with Voice URL\n${payload.voiceUrl}` : '(no Voice URL set; backend default will apply)'}?`;
      const proceed = window.confirm(confirmMsg);
      if (!proceed) {
        toast('Purchase cancelled');
        return;
      }
      const data = await postWithFallback('/api/twilio/purchase-number', payload);
      toast.success(`Purchased ${data.phoneNumber}`);
      await loadOwned();
    } catch (err) {
      const msg = err?.response?.data?.details || 'Failed to purchase number';
      toast.error(msg);
      console.error('Purchase error:', err?.response?.data || err);
    } finally {
      setPurchasing(null);
    }
  };

  const release = async (sid) => {
    try {
      await deleteWithFallback(`/api/twilio/numbers/${sid}`);
      toast.success('Number released');
      await loadOwned();
    } catch (err) {
      const msg = err?.response?.data?.details || 'Failed to release number';
      toast.error(msg);
      console.error('Release error:', err?.response?.data || err);
    }
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Phone Numbers</h1>
        <p className="text-gray-600 mt-2">Search and purchase Twilio numbers, and manage your existing numbers.</p>
      </div>

      {/* Search Panel */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Search className="h-6 w-6 text-primary-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900">Search Available Numbers</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Country (ISO)</label>
            <div className="flex items-center">
              <Globe className="h-4 w-4 text-gray-500 mr-2" />
              <input
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="US"
                maxLength={2}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={numberType}
              onChange={(e) => setNumberType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="local">Local</option>
              <option value="tollfree">Toll-Free</option>
              <option value="mobile">Mobile</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Area Code</label>
            <input
              type="text"
              value={areaCode}
              onChange={(e) => setAreaCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="415"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Contains</label>
            <input
              type="text"
              value={contains}
              onChange={(e) => setContains(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="e.g. *555*"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Limit</label>
            <input
              type="number"
              min="1"
              max="100"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 20)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="flex items-center space-x-6 mt-4">
          <label className="inline-flex items-center">
            <input type="checkbox" className="form-checkbox h-4 w-4 text-primary-600" checked={voiceEnabled} onChange={(e) => setVoiceEnabled(e.target.checked)} />
            <span className="ml-2 text-sm">Voice Enabled</span>
          </label>
          <label className="inline-flex items-center">
            <input type="checkbox" className="form-checkbox h-4 w-4 text-primary-600" checked={smsEnabled} onChange={(e) => setSmsEnabled(e.target.checked)} />
            <span className="ml-2 text-sm">SMS Enabled</span>
          </label>
          <label className="inline-flex items-center">
            <input type="checkbox" className="form-checkbox h-4 w-4 text-primary-600" checked={mmsEnabled} onChange={(e) => setMmsEnabled(e.target.checked)} />
            <span className="ml-2 text-sm">MMS Enabled</span>
          </label>
        </div>

        <div className="mt-6">
          <button
            onClick={search}
            disabled={searching}
            className="flex items-center px-5 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${searching ? 'animate-spin' : ''}`} />
            {searching ? 'Searching...' : 'Search Numbers'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <ListChecks className="h-6 w-6 text-primary-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900">Results</h2>
          <span className="ml-2 text-sm text-gray-500">{available.length} numbers</span>
        </div>
        {available.length === 0 ? (
          <p className="text-gray-500">No numbers yet. Run a search.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {available.map((n) => (
              <div key={n.phoneNumber} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Phone className="h-5 w-5 text-primary-600 mr-2" />
                    <div>
                      <div className="font-semibold text-gray-900">{n.phoneNumber}</div>
                      <div className="text-xs text-gray-500">{n.locality || '—'} {n.region ? `· ${n.region}` : ''}</div>
                    </div>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-600">
                  <span className="mr-3">Voice: {n.capabilities?.voice ? 'Yes' : 'No'}</span>
                  <span className="mr-3">SMS: {n.capabilities?.SMS || n.capabilities?.sms ? 'Yes' : 'No'}</span>
                  <span>MMS: {n.capabilities?.MMS || n.capabilities?.mms ? 'Yes' : 'No'}</span>
                </div>
                <div className="mt-3">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Voice URL (optional)</label>
                  <input
                    type="url"
                    value={voiceUrlByNumber[n.phoneNumber] || ''}
                    onChange={(e) => setVoiceUrlByNumber(prev => ({ ...prev, [n.phoneNumber]: e.target.value }))}
                    placeholder={defaultVoiceUrl || 'https://your-ngrok.ngrok.app/voice'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                  />
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => purchase(n.phoneNumber)}
                    disabled={purchasing === n.phoneNumber}
                    className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition disabled:opacity-50"
                  >
                    <ShoppingCart className="h-4 w-4 mr-2" />
                    {purchasing === n.phoneNumber ? 'Purchasing...' : 'Purchase'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Owned Numbers */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Phone className="h-6 w-6 text-primary-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900">My Numbers</h2>
          <button
            onClick={loadOwned}
            className="ml-auto flex items-center px-3 py-1 text-sm border rounded hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </button>
        </div>
        {loadingOwned ? (
          <div className="text-gray-500">Loading...</div>
        ) : owned.length === 0 ? (
          <p className="text-gray-500">You don't own any numbers yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Number</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Friendly Name</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Voice URL</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {owned.map((n) => (
                  <tr key={n.sid}>
                    <td className="px-4 py-2 whitespace-nowrap font-medium">{n.phoneNumber}</td>
                    <td className="px-4 py-2 whitespace-nowrap">{n.friendlyName || '—'}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-600">
                      <div className="flex items-center space-x-2">
                        <a href={n.voiceUrl || '#'} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline truncate max-w-xs">
                          {n.voiceUrl || '—'}
                        </a>
                        <button
                          onClick={async () => {
                            const current = n.voiceUrl || '';
                            const input = window.prompt('Enter new Voice URL (leave blank to use NGROK_URL/voice):', current);
                            if (input === null) return; // cancelled
                            try {
                              await postWithFallback(`/api/twilio/numbers/${n.sid}/voice-url`, {
                                voiceUrl: input ? input.trim() : undefined,
                                voiceMethod: 'POST',
                              });
                              toast.success('Voice URL updated');
                              await loadOwned();
                            } catch (err) {
                              const msg = err?.response?.data?.details || 'Failed to update voice URL';
                              toast.error(msg);
                              console.error('Update voice URL error:', err?.response?.data || err);
                            }
                          }}
                          title="Change Voice URL"
                          className="inline-flex items-center px-2 py-1 border rounded hover:bg-gray-50"
                        >
                          <Link2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-right">
                      <button
                        onClick={() => release(n.sid)}
                        className="inline-flex items-center px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <Trash2 className="h-4 w-4 mr-1" /> Release
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Numbers;



