import React, { useState, useEffect } from 'react';
import { 
  User, 
  Mail, 
  Lock, 
  Save, 
  Edit3, 
  Eye, 
  EyeOff,
  CheckCircle,
  AlertCircle,
  Calendar,
  Shield,
  X
} from 'lucide-react';
import api from '../api';
import toast from 'react-hot-toast';

const Profile = () => {
  const [profile, setProfile] = useState({
    id: null,
    username: '',
    email: '',
    is_admin: false,
    created_at: '',
    last_login: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [profileForm, setProfileForm] = useState({
    username: '',
    email: ''
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/api/auth/me');
      if (data.authenticated && data.user) {
        setProfile(data.user);
        setProfileForm({
          username: data.user.username || '',
          email: data.user.email || ''
        });
      }
    } catch (error) {
      toast.error('Failed to load profile');
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await api.put('/api/auth/profile', profileForm);
      toast.success('Profile updated successfully');
      setEditing(false);
      await fetchProfile();
    } catch (error) {
      const message = error?.response?.data?.error || 'Failed to update profile';
      toast.error(message);
      console.error('Error updating profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordForm.newPassword.length < 6) {
      toast.error('New password must be at least 6 characters long');
      return;
    }

    try {
      setSaving(true);
      await api.put('/api/auth/change-password', {
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword
      });
      toast.success('Password changed successfully');
      closePasswordModal();
    } catch (error) {
      const message = error?.response?.data?.error || 'Failed to change password';
      toast.error(message);
      console.error('Error changing password:', error);
    } finally {
      setSaving(false);
    }
  };

  const openPasswordModal = () => {
    setShowPasswordModal(true);
    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
  };

  const closePasswordModal = () => {
    setShowPasswordModal(false);
    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    setShowPassword(false);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Profile</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">Manage your account information and security settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Profile Information */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center">
              <User className="h-5 w-5 text-primary-600 dark:text-primary-400 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Profile Information</h3>
            </div>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                <Edit3 className="h-4 w-4 mr-1" />
                Edit
              </button>
            )}
          </div>

          <div className="p-6">
            {editing ? (
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    value={profileForm.username}
                    onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={profileForm.email}
                    onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>

                <div className="flex items-center justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setEditing(false);
                      setProfileForm({
                        username: profile.username || '',
                        email: profile.email || ''
                      });
                    }}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {saving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center">
                  <User className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Username</p>
                    <p className="text-lg text-gray-900 dark:text-white">{profile.username || 'Not set'}</p>
                  </div>
                </div>

                <div className="flex items-center">
                  <Mail className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Email Address</p>
                    <p className="text-lg text-gray-900 dark:text-white">{profile.email || 'Not set'}</p>
                  </div>
                </div>

                <div className="flex items-center">
                  <Shield className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Account Type</p>
                    <p className="text-lg text-gray-900 dark:text-white">
                      {profile.is_admin ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                          <Shield className="h-3 w-3 mr-1" />
                          Administrator
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                          <User className="h-3 w-3 mr-1" />
                          User
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex items-center">
                  <Calendar className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Member Since</p>
                    <p className="text-lg text-gray-900 dark:text-white">{formatDate(profile.created_at)}</p>
                  </div>
                </div>

                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Login</p>
                    <p className="text-lg text-gray-900 dark:text-white">{formatDate(profile.last_login)}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Change Password */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <Lock className="h-5 w-5 text-primary-600 dark:text-primary-400 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Change Password</h3>
            </div>
          </div>

          <div className="p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock className="h-8 w-8 text-gray-400 dark:text-gray-500" />
              </div>
              <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Update Your Password
              </h4>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Keep your account secure by changing your password regularly
              </p>
              <button
                onClick={openPasswordModal}
                className="inline-flex items-center px-6 py-3 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
              >
                <Lock className="h-4 w-4 mr-2" />
                Change Password
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Security Tips */}
      <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-3 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">Security Tips</h4>
            <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <li>• Use a strong, unique password for your account</li>
              <li>• Never share your login credentials with anyone</li>
              <li>• Log out from shared or public computers</li>
              <li>• Contact support if you notice any suspicious activity</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div className="flex items-center">
                <Lock className="h-5 w-5 text-primary-600 dark:text-primary-400 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Change Password</h3>
              </div>
              <button
                onClick={closePasswordModal}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handlePasswordChange} className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Current Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={passwordForm.currentPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                    className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                    placeholder="Enter current password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                  minLength={6}
                  placeholder="Enter new password"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Must be at least 6 characters long</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                  minLength={6}
                  placeholder="Confirm new password"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closePasswordModal}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Changing...
                    </>
                  ) : (
                    <>
                      <Lock className="h-4 w-4 mr-2" />
                      Change Password
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
