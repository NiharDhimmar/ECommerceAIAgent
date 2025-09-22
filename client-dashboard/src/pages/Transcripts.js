import React, { useState, useEffect } from 'react';
import { FileText, Download, Search, User, Bot } from 'lucide-react';
import api from '../api';

const Transcripts = () => {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTranscript, setSelectedTranscript] = useState(null);

  useEffect(() => {
    fetchTranscripts();
  }, []);

  const fetchTranscripts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/client/transcripts');
      if (response.data.ok) {
        setTranscripts(response.data.transcripts);
      }
    } catch (error) {
      console.error('Failed to fetch transcripts:', error);
      // Set mock data for demonstration
      setTranscripts([
        {
          id: 1,
          callId: 'CA1234567890',
          phoneNumber: '+1234567890',
          timestamp: '2024-01-15 14:30:00',
          intent: 'Customer Support',
          duration: '2:45',
          conversation: [
            { speaker: 'customer', text: 'Hello, I need help with my order.', timestamp: '14:30:15' },
            { speaker: 'ai', text: 'Hello! I\'d be happy to help you with your order. Can you please provide your order number?', timestamp: '14:30:18' },
            { speaker: 'customer', text: 'Sure, it\'s ORD-12345.', timestamp: '14:30:25' },
            { speaker: 'ai', text: 'Thank you! I can see your order is currently being processed and should ship within 2 business days.', timestamp: '14:30:28' },
            { speaker: 'customer', text: 'Great! When will I receive a tracking number?', timestamp: '14:30:35' },
            { speaker: 'ai', text: 'You\'ll receive a tracking number via email once your order ships. Is there anything else I can help you with?', timestamp: '14:30:38' },
            { speaker: 'customer', text: 'No, that\'s all. Thank you!', timestamp: '14:30:42' },
            { speaker: 'ai', text: 'You\'re welcome! Have a great day!', timestamp: '14:30:45' }
          ]
        },
        {
          id: 2,
          callId: 'CA1987654321',
          phoneNumber: '+1987654321',
          timestamp: '2024-01-15 13:15:00',
          intent: 'Product Inquiry',
          duration: '1:20',
          conversation: [
            { speaker: 'customer', text: 'Hi, I\'m interested in your premium package.', timestamp: '13:15:10' },
            { speaker: 'ai', text: 'Hello! I\'d be happy to tell you about our premium package. What specific features are you most interested in?', timestamp: '13:15:13' },
            { speaker: 'customer', text: 'I want to know about the advanced analytics and reporting features.', timestamp: '13:15:20' },
            { speaker: 'ai', text: 'Our premium package includes comprehensive analytics, custom reports, and real-time dashboards. Would you like me to send you detailed information?', timestamp: '13:15:23' },
            { speaker: 'customer', text: 'Yes, please send that to my email.', timestamp: '13:15:30' },
            { speaker: 'ai', text: 'Perfect! I\'ll send you the premium package details right away. Is there anything else I can help you with today?', timestamp: '13:15:33' }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (transcript) => {
    const content = `Call ID: ${transcript.callId}
Phone Number: ${transcript.phoneNumber}
Date: ${new Date(transcript.timestamp).toLocaleString()}
Intent: ${transcript.intent}
Duration: ${transcript.duration}

Conversation:
${transcript.conversation.map(msg => 
  `[${msg.timestamp}] ${msg.speaker.toUpperCase()}: ${msg.text}`
).join('\n')}`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `transcript_${transcript.callId}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const filteredTranscripts = transcripts.filter(transcript =>
    transcript.phoneNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transcript.intent.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transcript.callId.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Transcripts</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">View and download conversation transcripts</p>
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search transcripts by phone number, intent, or call ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Transcripts List */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Transcripts ({filteredTranscripts.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-96 overflow-y-auto">
              {filteredTranscripts.length === 0 ? (
                <div className="p-6 text-center">
                  <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No transcripts found</p>
                </div>
              ) : (
                filteredTranscripts.map((transcript) => (
                  <div
                    key={transcript.id}
                    onClick={() => setSelectedTranscript(transcript)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      selectedTranscript?.id === transcript.id ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {transcript.phoneNumber}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {transcript.duration}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      {transcript.intent}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(transcript.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Conversation View */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Conversation</h3>
              {selectedTranscript && (
                <button
                  onClick={() => handleDownload(selectedTranscript)}
                  className="flex items-center space-x-2 px-3 py-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
                >
                  <Download className="h-4 w-4" />
                  <span>Download</span>
                </button>
              )}
            </div>
            <div className="p-6 max-h-96 overflow-y-auto">
              {selectedTranscript ? (
                <div className="space-y-4">
                  {selectedTranscript.conversation.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.speaker === 'customer' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.speaker === 'customer'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                        }`}
                      >
                        <div className="flex items-center space-x-2 mb-1">
                          {message.speaker === 'customer' ? (
                            <User className="h-3 w-3" />
                          ) : (
                            <Bot className="h-3 w-3" />
                          )}
                          <span className="text-xs opacity-75">
                            {message.speaker === 'customer' ? 'Customer' : 'AI Assistant'}
                          </span>
                          <span className="text-xs opacity-75">{message.timestamp}</span>
                        </div>
                        <p className="text-sm">{message.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">Select a transcript to view the conversation</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Transcripts;
