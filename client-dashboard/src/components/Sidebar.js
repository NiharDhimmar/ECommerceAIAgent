import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  BarChart3, 
  Phone, 
  Mic, 
  FileText, 
  User,
  Menu,
  X
} from 'lucide-react';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: BarChart3 },
    { name: 'My Calls', href: '/calls', icon: Phone },
    { name: 'Recordings', href: '/recordings', icon: Mic },
    { name: 'Transcripts', href: '/transcripts', icon: FileText },
    { name: 'Profile', href: '/profile', icon: User },
  ];

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <>
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-lg bg-primary-600 text-white shadow-lg"
        >
          {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-72 xl:w-80 bg-gradient-to-b from-primary-700 to-primary-900 dark:from-gray-800 dark:to-gray-900 shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Brand/Logo */}
        <div className="flex items-center justify-center h-20 bg-gradient-to-r from-primary-700 to-primary-800 dark:from-gray-800 dark:to-gray-700 border-b border-primary-900 dark:border-gray-600">
          <div className="text-center">
            <span className="text-white text-2xl font-extrabold tracking-wide">AgentAI</span>
            <p className="text-primary-200 dark:text-gray-300 text-xs mt-1">Client Portal</p>
          </div>
        </div>
        
        <nav className="mt-8 flex-1">
          <div className="px-6 space-y-3">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center px-4 py-4 text-base font-medium rounded-xl transition-all duration-200 group relative
                    ${isActive(item.href)
                      ? 'bg-white dark:bg-gray-700 text-primary-800 dark:text-white shadow-lg border-l-4 border-primary-500 transform scale-105'
                      : 'text-white dark:text-gray-200 hover:bg-primary-600 dark:hover:bg-gray-700 hover:text-white dark:hover:text-white hover:transform hover:scale-105 hover:shadow-md'
                    }
                  `}
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className={`mr-4 h-6 w-6 ${isActive(item.href) ? 'text-primary-600 dark:text-primary-400' : 'text-white dark:text-gray-200 group-hover:text-white'}`} />
                  <span className="truncate font-semibold">{item.name}</span>
                  {isActive(item.href) && (
                    <div className="absolute right-2 w-2 h-2 bg-primary-500 dark:bg-primary-400 rounded-full"></div>
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-6 border-t border-primary-900 dark:border-gray-600">
          <div className="text-center">
            <p className="text-primary-200 dark:text-gray-300 text-xs">
              AgentAI Client Portal
            </p>
            <p className="text-primary-300 dark:text-gray-400 text-xs mt-1">
              Version 1.0.0
            </p>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
