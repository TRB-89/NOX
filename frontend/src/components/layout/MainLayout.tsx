import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const MainLayout: React.FC = () => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const location = useLocation();

  // Map route to page title and subtitle
  const getHeaderInfo = () => {
    switch (location.pathname) {
      case '/':
        return {
          title: 'Mission Overview',
          subtitle: 'Live Neural Intrusion Telemetry & System Status',
        };
      case '/detect':
        return {
          title: 'Neural Detection Engine',
          subtitle: 'Direct Flow Classification & Bounded CSV Dataset Ingestion',
        };
      case '/analytics':
        return {
          title: 'Threat Analytics',
          subtitle: 'Empirical Distribution & Offline Model Benchmark Metrics',
        };
      case '/history':
        return {
          title: 'Detection History',
          subtitle: 'Immutable SQLite Security Incident Records',
        };
      case '/system':
        return {
          title: 'System Information',
          subtitle: 'Neural Architecture, Preprocessing Pipeline & Benchmark Specifications',
        };
      default:
        return {
          title: 'NØX Terminal',
          subtitle: 'Neural Intrusion Detection System',
        };
    }
  };

  const { title, subtitle } = getHeaderInfo();

  return (
    <div className="min-h-screen bg-background text-chrome flex">
      {/* Desktop & Mobile Sidebar */}
      <Sidebar
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col lg:pl-72 min-w-0">
        <Header
          title={title}
          subtitle={subtitle}
          onOpenMobileNav={() => setMobileNavOpen(true)}
        />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
