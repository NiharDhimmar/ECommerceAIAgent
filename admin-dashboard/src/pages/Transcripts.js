import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Download, 
  Eye,
  FileText,
  User,
  Bot,
  X
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Transcripts = () => {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchTranscripts();
  }, []);

  const fetchTranscripts = async () => {
    try {
      setLoading(true);
      const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';
      const { data } = await axios.get(`${API_BASE}/api/transcripts`);
      setTranscripts(data || []);
    } catch (error) {
      toast.error('Failed to load transcripts');
      console.error('Error fetching transcripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTranscripts = transcripts.filter(transcript => 
    transcript.callId.includes(searchTerm) || 
    (transcript.phoneNumber || '').includes(searchTerm) ||
    (transcript.fromNumber || '').includes(searchTerm) ||
    (transcript.toNumber || '').includes(searchTerm)
  );

  const totalPages = Math.max(1, Math.ceil(filteredTranscripts.length / pageSize));
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentItems = filteredTranscripts.slice(startIndex, endIndex);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, transcripts, pageSize]);

  const handleDownload = (transcript) => {
    const content = `Call Transcript: ${transcript.callId}\nTimestamp: ${transcript.timestamp}\nFrom: ${transcript.fromNumber || ''}\nTo: ${transcript.toNumber || ''}\n\nConversation:\n${transcript.conversation.map(msg => `[${msg.time}] ${msg.speaker.toUpperCase()}: ${msg.message}`).join('\n')}`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = transcript.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Transcript downloaded');
  };

  // Removed confidence display

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
        <h1 className="text-3xl font-bold text-gray-900">Transcripts</h1>
        <p className="text-gray-600 mt-2">View and manage conversation transcripts</p>
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

      {/* Transcripts Table */}
      {filteredTranscripts.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="max-h-[70vh] overflow-auto rounded-t-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call ID</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">From</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">To</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Messages</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {currentItems.map((transcript) => (
                  <tr key={transcript.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900 break-all">{transcript.callId}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{transcript.fromNumber || ''}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{transcript.toNumber || ''}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{transcript.timestamp}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{transcript.conversation.length}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => setSelectedTranscript(transcript)}
                          className="flex items-center px-3 py-1.5 bg-primary-600 text-white text-xs font-medium rounded-md hover:bg-primary-700"
                        >
                          <Eye className="h-4 w-4 mr-1" /> View
                        </button>
                        <button
                          onClick={() => handleDownload(transcript)}
                          className="flex items-center px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-md hover:bg-green-700"
                        >
                          <Download className="h-4 w-4 mr-1" /> Download
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
              Showing {filteredTranscripts.length === 0 ? 0 : startIndex + 1}-{Math.min(endIndex, filteredTranscripts.length)} of {filteredTranscripts.length}
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

      {filteredTranscripts.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No transcripts found</h3>
          <p className="text-gray-500">No transcripts match your search criteria.</p>
        </div>
      )}

      {/* Full Transcript Modal */}
      {selectedTranscript && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Full Transcript - {selectedTranscript.callId}</h3>
                <button
                  onClick={() => setSelectedTranscript(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="text-sm font-medium text-gray-500">Call ID</label>
                  <p className="text-sm text-gray-900">{selectedTranscript.callId}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">From</label>
                  <p className="text-sm text-gray-900">{selectedTranscript.fromNumber || ''}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">To</label>
                  <p className="text-sm text-gray-900">{selectedTranscript.toNumber || ''}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Timestamp</label>
                  <p className="text-sm text-gray-900">{selectedTranscript.timestamp}</p>
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Full Conversation</h4>
                <div className="space-y-3">
                  {selectedTranscript.conversation.map((msg, index) => (
                    <div key={index} className={`flex items-start ${msg.speaker === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        msg.speaker === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <div className="flex items-center mb-1">
                          {msg.speaker === 'user' ? (
                            <User className="h-3 w-3 mr-1" />
                          ) : (
                            <Bot className="h-3 w-3 mr-1" />
                          )}
                          <span className="text-xs font-medium">
                            {msg.speaker === 'user' ? 'Customer' : 'AI Assistant'}
                          </span>
                          <span className="text-xs ml-2 opacity-75">{msg.time}</span>
                        </div>
                        <p className="text-sm">{msg.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Transcripts; 