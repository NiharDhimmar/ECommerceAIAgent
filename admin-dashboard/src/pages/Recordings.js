import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  Search, 
  Download, 
  Play, 
  Pause
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Recordings = () => {
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [playingId, setPlayingId] = useState(null);
  const [loadingAudio, setLoadingAudio] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const audioRefs = useRef({});

  useEffect(() => {
    fetchRecordings();
  }, []);

  // Cleanup audio when component unmounts
  useEffect(() => {
    return () => {
      // Stop all audio when component unmounts
      Object.values(audioRefs.current).forEach(audio => {
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
        }
      });
    };
  }, []);

  const fetchRecordings = async () => {
    try {
      setLoading(true);
      const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';
      const { data } = await axios.get(`${API_BASE}/api/recordings`);
      const apiBase = API_BASE;
      const normalized = (data || []).map((r) => ({
        ...r,
        url: r.url && r.url.startsWith('http') ? r.url : `${apiBase}${r.url || ''}`,
      }));
      setRecordings(normalized);
    } catch (error) {
      toast.error('Failed to load recordings');
      console.error('Error fetching recordings:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredRecordings = recordings.filter(recording => 
    (recording.callId || '').includes(searchTerm) || 
    (recording.phoneNumber || '').includes(searchTerm) ||
    (recording.fromNumber || '').includes(searchTerm) ||
    (recording.toNumber || '').includes(searchTerm) ||
    (recording.intent || '').toLowerCase().includes((searchTerm || '').toLowerCase())
  );
  const totalPages = Math.max(1, Math.ceil(filteredRecordings.length / pageSize));
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentItems = filteredRecordings.slice(startIndex, endIndex);
  
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, recordings, pageSize]);

  const handlePlay = async (recordingId) => {
    try {
      setLoadingAudio(recordingId);
      
      // Stop any currently playing audio
      if (playingId && playingId !== recordingId) {
        const currentAudio = audioRefs.current[playingId];
        if (currentAudio) {
          currentAudio.pause();
          currentAudio.currentTime = 0;
        }
      }

      setPlayingId(recordingId);
      const audio = audioRefs.current[recordingId];
      if (audio) {
        // Add a small delay to ensure previous audio is fully stopped
        await new Promise(resolve => setTimeout(resolve, 100));
        await audio.play();
      }
    } catch (error) {
      console.error('Error playing audio:', error);
      setPlayingId(null);
      toast.error('Failed to play audio');
    } finally {
      setLoadingAudio(null);
    }
  };

  const handlePause = (recordingId) => {
    try {
      setPlayingId(null);
      const audio = audioRefs.current[recordingId];
      if (audio) {
        audio.pause();
      }
    } catch (error) {
      console.error('Error pausing audio:', error);
    }
  };

  const handleAudioEnded = (recordingId) => {
    setPlayingId(null);
  };

  const handleDownload = (recording) => {
    const link = document.createElement('a');
    link.href = recording.url;
    link.download = recording.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Download started');
  };

  const formatDuration = (duration) => {
    return duration;
  };

  const formatFileSize = (size) => {
    return size;
  };

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
        <h1 className="text-3xl font-bold text-gray-900">Recordings</h1>
        <p className="text-gray-600 mt-2">Manage and playback call recordings</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search by call ID, phonenumbers..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Recordings Table */}
      {filteredRecordings.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="max-h-[70vh] overflow-auto rounded-t-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">From</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">To</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {currentItems.map((recording) => (
                  <tr key={recording.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 break-all">{recording.callId}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{recording.fromNumber || ''}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{recording.toNumber || ''}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{recording.timestamp}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{formatDuration(recording.duration)}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{formatFileSize(recording.size)}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {/* Hidden audio element per row */}
                      <audio
                        ref={(el) => {
                          if (el) {
                            audioRefs.current[recording.id] = el;
                          }
                        }}
                        onEnded={() => handleAudioEnded(recording.id)}
                        onError={() => {
                          console.error('Audio error for recording:', recording.id);
                          setPlayingId(null);
                        }}
                        preload="metadata"
                        className="hidden"
                      >
                        <source src={recording.url} type="audio/mpeg" />
                      </audio>
                      <div className="flex justify-end space-x-2">
                        {playingId === recording.id ? (
                          <button
                            onClick={() => handlePause(recording.id)}
                            className="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-md hover:bg-red-700"
                          >
                            <Pause className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handlePlay(recording.id)}
                            disabled={loadingAudio === recording.id}
                            className="px-3 py-1.5 bg-primary-600 text-white text-xs font-medium rounded-md hover:bg-primary-700 disabled:opacity-50"
                          >
                            {loadingAudio === recording.id ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </button>
                        )}
                        <button
                          onClick={() => handleDownload(recording)}
                          className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-md hover:bg-green-700"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              Showing {filteredRecordings.length === 0 ? 0 : startIndex + 1}-{Math.min(endIndex, filteredRecordings.length)} of {filteredRecordings.length}
            </div>
            <div className="flex items-center space-x-3">
              <select
                className="border border-gray-300 rounded-md text-sm px-2 py-1"
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
              >
                <option value={10}>10 / page</option>
                <option value={25}>25 / page</option>
                <option value={50}>50 / page</option>
              </select>
              <div className="flex items-center space-x-2">
                <button
                  className="px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-50"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  Prev
                </button>
                <span className="text-sm text-gray-700">Page {currentPage} of {totalPages}</span>
                <button
                  className="px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-50"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {filteredRecordings.length === 0 && (
        <div className="text-center py-12">
          <Mic className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No recordings found</h3>
          <p className="text-gray-500">No recordings match your search criteria.</p>
        </div>
      )}
    </div>
  );
};

export default Recordings; 