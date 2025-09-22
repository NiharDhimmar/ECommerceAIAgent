import React, { useState, useEffect } from 'react';
import { Mic, Play, Pause, Download, Search } from 'lucide-react';
import api from '../api';

const Recordings = () => {
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [playingId, setPlayingId] = useState(null);
  const [audioRefs, setAudioRefs] = useState({});

  useEffect(() => {
    fetchRecordings();
  }, []);

  const fetchRecordings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/client/recordings');
      if (response.data.ok) {
        setRecordings(response.data.recordings);
      }
    } catch (error) {
      console.error('Failed to fetch recordings:', error);
      // Set mock data for demonstration
      setRecordings([
        {
          id: 1,
          callId: 'CA1234567890',
          phoneNumber: '+1234567890',
          duration: '2:45',
          timestamp: '2024-01-15 14:30:00',
          intent: 'Customer Support',
          fileSize: '1.2 MB',
          url: '/recordings/sample1.mp3'
        },
        {
          id: 2,
          callId: 'CA1987654321',
          phoneNumber: '+1987654321',
          duration: '1:20',
          timestamp: '2024-01-15 13:15:00',
          intent: 'Product Inquiry',
          fileSize: '0.8 MB',
          url: '/recordings/sample2.mp3'
        },
        {
          id: 3,
          callId: 'CA1122334455',
          phoneNumber: '+1122334455',
          duration: '0:45',
          timestamp: '2024-01-15 12:00:00',
          intent: 'Technical Issue',
          fileSize: '0.4 MB',
          url: '/recordings/sample3.mp3'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = (recordingId) => {
    const audio = audioRefs[recordingId];
    if (!audio) return;

    if (playingId === recordingId) {
      audio.pause();
      setPlayingId(null);
    } else {
      // Pause any currently playing audio
      if (playingId && audioRefs[playingId]) {
        audioRefs[playingId].pause();
      }
      audio.play();
      setPlayingId(recordingId);
    }
  };

  const handleDownload = (recording) => {
    // In a real application, this would download the actual file
    const link = document.createElement('a');
    link.href = recording.url;
    link.download = `recording_${recording.callId}.mp3`;
    link.click();
  };

  const filteredRecordings = recordings.filter(recording =>
    recording.phoneNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recording.intent.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recording.callId.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-gray-200 dark:bg-gray-700 rounded-lg h-48"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Recordings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">Listen to and download your call recordings</p>
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search recordings by phone number, intent, or call ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>

      {/* Recordings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredRecordings.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Mic className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No recordings found</p>
          </div>
        ) : (
          filteredRecordings.map((recording) => (
            <div key={recording.id} className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Mic className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {recording.callId}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {recording.fileSize}
                  </span>
                </div>

                <div className="mb-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    {recording.phoneNumber}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {recording.intent}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(recording.timestamp).toLocaleDateString()} {new Date(recording.timestamp).toLocaleTimeString()}
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handlePlayPause(recording.id)}
                      className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                    >
                      {playingId === recording.id ? (
                        <Pause className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </button>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {recording.duration}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDownload(recording)}
                    className="p-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>

                {/* Hidden audio element */}
                <audio
                  ref={(el) => {
                    if (el) {
                      setAudioRefs(prev => ({ ...prev, [recording.id]: el }));
                    }
                  }}
                  src={recording.url}
                  onEnded={() => setPlayingId(null)}
                  onPause={() => setPlayingId(null)}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Recordings;
