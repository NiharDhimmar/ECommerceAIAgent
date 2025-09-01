import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Save, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  Phone,
  Mic,
  Shield,
  Database,
  Globe
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Settings = () => {
  const [settings, setSettings] = useState({
    twilio: {
      accountSid: '',
      authToken: '',
      fromNumber: '',
      toNumber: '',
      ngrokUrl: ''
    },
    ai: {
      confidenceThreshold: 0.85,
      maxResponseTime: 5000,
      enableRecording: true,
      enableTranscripts: true
    },
    system: {
      humanAgentNumber: '',
      maxCallDuration: 3600,
      enableCallForwarding: true,
      enableAnalytics: true
    },
    security: {
      enableHttps: true,
      sessionTimeout: 3600,
      maxLoginAttempts: 5,
      enableAuditLog: true
    }
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      // Mock data - in real app, fetch from Flask API
      const mockSettings = {
        twilio: {
          accountSid: 'AC1234567890abcdef',
          authToken: '••••••••••••••••••••••••••••••••',
          fromNumber: '+1234567890',
          toNumber: '+1234567891',
          ngrokUrl: 'https://your-ngrok-url.ngrok.io'
        },
        ai: {
          confidenceThreshold: 0.85,
          maxResponseTime: 5000,
          enableRecording: true,
          enableTranscripts: true
        },
        system: {
          humanAgentNumber: '+1234567892',
          maxCallDuration: 3600,
          enableCallForwarding: true,
          enableAnalytics: true
        },
        security: {
          enableHttps: true,
          sessionTimeout: 3600,
          maxLoginAttempts: 5,
          enableAuditLog: true
        }
      };
      
      setSettings(mockSettings);
    } catch (error) {
      toast.error('Failed to load settings');
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      // In real app, save to Flask API
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error('Failed to save settings');
      console.error('Error saving settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setLoading(true);
      // In real app, test Twilio connection
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      toast.success('Connection test successful');
    } catch (error) {
      toast.error('Connection test failed');
      console.error('Error testing connection:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const SettingSection = ({ title, icon: Icon, children }) => (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center mb-4">
        <Icon className="h-6 w-6 text-primary-600 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      {children}
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
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Configure your Voice AI system</p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
        {/* Twilio Configuration */}
        <SettingSection title="Twilio Configuration" icon={Phone}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Account SID
              </label>
              <input
                type="text"
                value={settings.twilio.accountSid}
                onChange={(e) => updateSetting('twilio', 'accountSid', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="AC1234567890abcdef"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auth Token
              </label>
              <input
                type="password"
                value={settings.twilio.authToken}
                onChange={(e) => updateSetting('twilio', 'authToken', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••••••••••••••••••••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Number
              </label>
              <input
                type="text"
                value={settings.twilio.fromNumber}
                onChange={(e) => updateSetting('twilio', 'fromNumber', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="+1234567890"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Number
              </label>
              <input
                type="text"
                value={settings.twilio.toNumber}
                onChange={(e) => updateSetting('twilio', 'toNumber', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="+1234567891"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ngrok URL
              </label>
              <input
                type="url"
                value={settings.twilio.ngrokUrl}
                onChange={(e) => updateSetting('twilio', 'ngrokUrl', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="https://your-ngrok-url.ngrok.io"
              />
            </div>
          </div>
          <div className="mt-4">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Test Connection
            </button>
          </div>
        </SettingSection>

        {/* AI Configuration */}
        <SettingSection title="AI Configuration" icon={Mic}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confidence Threshold
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.ai.confidenceThreshold}
                onChange={(e) => updateSetting('ai', 'confidenceThreshold', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0.0</span>
                <span>{settings.ai.confidenceThreshold}</span>
                <span>1.0</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Response Time (ms)
              </label>
              <input
                type="number"
                value={settings.ai.maxResponseTime}
                onChange={(e) => updateSetting('ai', 'maxResponseTime', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                min="1000"
                max="10000"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enableRecording"
                checked={settings.ai.enableRecording}
                onChange={(e) => updateSetting('ai', 'enableRecording', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="enableRecording" className="ml-2 text-sm text-gray-700">
                Enable Call Recording
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enableTranscripts"
                checked={settings.ai.enableTranscripts}
                onChange={(e) => updateSetting('ai', 'enableTranscripts', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="enableTranscripts" className="ml-2 text-sm text-gray-700">
                Enable Transcripts
              </label>
            </div>
          </div>
        </SettingSection>

        {/* System Configuration */}
        <SettingSection title="System Configuration" icon={Database}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Human Agent Number
              </label>
              <input
                type="text"
                value={settings.system.humanAgentNumber}
                onChange={(e) => updateSetting('system', 'humanAgentNumber', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="+1234567892"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Call Duration (seconds)
              </label>
              <input
                type="number"
                value={settings.system.maxCallDuration}
                onChange={(e) => updateSetting('system', 'maxCallDuration', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                min="60"
                max="7200"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enableCallForwarding"
                checked={settings.system.enableCallForwarding}
                onChange={(e) => updateSetting('system', 'enableCallForwarding', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="enableCallForwarding" className="ml-2 text-sm text-gray-700">
                Enable Call Forwarding
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enableAnalytics"
                checked={settings.system.enableAnalytics}
                onChange={(e) => updateSetting('system', 'enableAnalytics', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="enableAnalytics" className="ml-2 text-sm text-gray-700">
                Enable Analytics
              </label>
            </div>
          </div>
        </SettingSection>

        {/* Security Configuration */}
        <SettingSection title="Security Configuration" icon={Shield}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enableHttps"
                checked={settings.security.enableHttps}
                onChange={(e) => updateSetting('security', 'enableHttps', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="enableHttps" className="ml-2 text-sm text-gray-700">
                Enable HTTPS Only
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Session Timeout (seconds)
              </label>
              <input
                type="number"
                value={settings.security.sessionTimeout}
                onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                min="300"
                max="86400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Login Attempts
              </label>
              <input
                type="number"
                value={settings.security.maxLoginAttempts}
                onChange={(e) => updateSetting('security', 'maxLoginAttempts', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                min="3"
                max="10"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enableAuditLog"
                checked={settings.security.enableAuditLog}
                onChange={(e) => updateSetting('security', 'enableAuditLog', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="enableAuditLog" className="ml-2 text-sm text-gray-700">
                Enable Audit Logging
              </label>
            </div>
          </div>
        </SettingSection>

        {/* Save Button */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={fetchSettings}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Settings; 