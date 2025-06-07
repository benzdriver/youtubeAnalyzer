'use client';

import React from 'react';

interface Tab {
  id: string;
  label: string;
  icon?: string;
  content: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
  variant?: 'default' | 'pills' | 'underline';
  size?: 'sm' | 'md' | 'lg';
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onTabChange,
  className = '',
  variant = 'default',
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'text-sm px-3 py-2',
    md: 'text-base px-4 py-3',
    lg: 'text-lg px-6 py-4'
  };

  const getTabClasses = (tab: Tab) => {
    const baseClasses = `${sizeClasses[size]} font-medium transition-all duration-200 cursor-pointer flex items-center space-x-2`;
    const isActive = activeTab === tab.id;
    const isDisabled = tab.disabled;

    if (isDisabled) {
      return `${baseClasses} text-gray-400 cursor-not-allowed`;
    }

    switch (variant) {
      case 'pills':
        return `${baseClasses} rounded-lg ${
          isActive 
            ? 'bg-blue-600 text-white shadow-md' 
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }`;
      
      case 'underline':
        return `${baseClasses} border-b-2 ${
          isActive 
            ? 'border-blue-600 text-blue-600' 
            : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
        }`;
      
      default:
        return `${baseClasses} border-b ${
          isActive 
            ? 'border-blue-600 text-blue-600 bg-blue-50' 
            : 'border-gray-200 text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`;
    }
  };

  const getContentClasses = () => {
    switch (variant) {
      case 'pills':
        return 'mt-4';
      case 'underline':
        return 'mt-4 pt-4';
      default:
        return 'border-t border-gray-200 bg-white';
    }
  };

  const activeTabContent = tabs.find(tab => tab.id === activeTab)?.content;

  return (
    <div className={`w-full ${className}`}>
      <div className={`flex ${variant === 'pills' ? 'space-x-2' : ''} ${
        variant === 'default' ? 'border-b border-gray-200' : ''
      }`}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && onTabChange(tab.id)}
            className={getTabClasses(tab)}
            disabled={tab.disabled}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            id={`tab-${tab.id}`}
          >
            {tab.icon && <span>{tab.icon}</span>}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      <div
        className={getContentClasses()}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
        id={`tabpanel-${activeTab}`}
      >
        {activeTabContent}
      </div>
    </div>
  );
};

export default Tabs;
