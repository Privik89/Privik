import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  EnvelopeIcon,
  ExclamationTriangleIcon,
  UsersIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Email Analysis', href: '/emails', icon: EnvelopeIcon },
  { name: 'Threat Intelligence', href: '/threats', icon: ExclamationTriangleIcon },
  { name: 'Incidents', href: '/incidents', icon: ExclamationTriangleIcon },
  { name: 'User Risk', href: '/users', icon: UsersIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

function Sidebar() {
  return (
    <div className="flex flex-col w-64 bg-white shadow-lg">
      {/* Logo */}
      <div className="flex items-center justify-center h-16 px-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <ShieldCheckIcon className="h-8 w-8 text-privik-blue-600" />
          <span className="text-xl font-bold text-gray-900">Privik</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                isActive
                  ? 'bg-privik-blue-50 text-privik-blue-700 border-r-2 border-privik-blue-600'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="mr-3 h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          Privik v0.1.0
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
