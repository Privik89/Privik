import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  EnvelopeIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

function Sidebar() {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Email Analysis', href: '/emails', icon: EnvelopeIcon },
    { name: 'Threat Intelligence', href: '/threats', icon: ShieldCheckIcon },
    { name: 'Incidents', href: '/incidents', icon: ExclamationTriangleIcon },
    { name: 'User Risk', href: '/users', icon: UserGroupIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  ];

  return (
    <div className="flex flex-col w-64 bg-white shadow-lg">
      {/* Logo */}
      <div className="flex items-center justify-center h-16 bg-blue-600">
        <h1 className="text-white text-xl font-bold">Privik</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                isActive
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <p>Privik Email Security</p>
          <p>Version 1.0.0</p>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;