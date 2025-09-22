import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  User, 
  Settings, 
  LogOut, 
  ChevronDown,
  Bell,
  Sun,
  Moon
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';

const Header = () => {
  const [user, setUser] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [logoutLoading, setLogoutLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserProfile();
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
      applyTheme(savedTheme);
    }
  }, []);

  const fetchUserProfile = async () => {
    try {
      const { data } = await api.get('/api/auth/me');
      if (data.authenticated && data.user) {
        setUser(data.user);
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const handleLogout = async () => {
    try {
      setLogoutLoading(true);
      await api.post('/api/auth/logout');
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, redirect to login
      toast.error('Logout failed, but redirecting to login');
      navigate('/login');
    } finally {
      setLogoutLoading(false);
    }
  };

  const toggleProfileDropdown = () => {
    setIsProfileOpen(!isProfileOpen);
  };

  const toggleDarkMode = () => {
    const newTheme = isDarkMode ? 'light' : 'dark';
    setIsDarkMode(!isDarkMode);
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
    toast.success(`Switched to ${newTheme} mode`);
  };

  const applyTheme = (theme) => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isProfileOpen && !event.target.closest('.profile-dropdown')) {
        setIsProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isProfileOpen]);

  const getUserInitials = (username) => {
    if (!username) return 'U';
    return username.substring(0, 2).toUpperCase();
  };

  return (
    <header className="bg-white dark:bg-gray-800 shadow-lg border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left side - Page title or breadcrumbs can go here */}
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              AgentAI Operations Dashboard
            </h1>
          </div>

          {/* Right side - Actions and Profile */}
          <div className="flex items-center space-x-4">
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>

            {/* Notifications */}
            <button className="relative p-2 text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Bell className="h-5 w-5" />
              {/* Notification badge */}
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                3
              </span>
            </button>

            {/* Profile Dropdown */}
            <div className="relative profile-dropdown">
              <button
                onClick={toggleProfileDropdown}
                className="flex items-center space-x-3 p-2 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                    {getUserInitials(user?.username)}
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {user?.username || 'User'}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {user?.is_admin ? 'Administrator' : 'User'}
                    </p>
                  </div>
                </div>
                <ChevronDown className={`h-4 w-4 text-gray-400 dark:text-gray-300 transition-transform ${isProfileOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown Menu */}
              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-2 z-50">
                  {/* User Info Header */}
                  <div className="px-4 py-4 border-b border-gray-100 dark:border-gray-700 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-gray-700 dark:to-gray-600">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center text-white font-semibold">
                        {getUserInitials(user?.username)}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900 dark:text-white">
                          {user?.username || 'User'}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-300">
                          {user?.email || 'No email'}
                        </p>
                        {user?.is_admin && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 mt-1">
                            <Settings className="h-3 w-3 mr-1" />
                            Administrator
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Menu Items */}
                  <div className="py-2">
                    <Link
                      to="/profile"
                      className="flex items-center px-4 py-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      onClick={() => setIsProfileOpen(false)}
                    >
                      <User className="h-4 w-4 mr-3 text-gray-400 dark:text-gray-500" />
                      <div>
                        <p className="font-medium">View Profile</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Manage your account</p>
                      </div>
                    </Link>
                    
                    <Link
                      to="/settings"
                      className="flex items-center px-4 py-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      onClick={() => setIsProfileOpen(false)}
                    >
                      <Settings className="h-4 w-4 mr-3 text-gray-400 dark:text-gray-500" />
                      <div>
                        <p className="font-medium">Settings</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">App preferences</p>
                      </div>
                    </Link>
                  </div>

                  {/* Logout */}
                  <div className="border-t border-gray-100 dark:border-gray-700 pt-2">
                    <button
                      onClick={handleLogout}
                      disabled={logoutLoading}
                      className="w-full flex items-center px-4 py-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                    >
                      <LogOut className="h-4 w-4 mr-3" />
                      <div>
                        <p className="font-medium">
                          {logoutLoading ? 'Logging out...' : 'Logout'}
                        </p>
                        <p className="text-xs text-red-500 dark:text-red-400">Sign out of your account</p>
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
