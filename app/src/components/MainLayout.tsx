"use client";

import React, { useEffect, useState } from 'react';
import { useAppContext } from './AppContext';
import Welcome from './Welcome';
import Login from './Login';
import Sidebar from './Sidebar';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const { isOnboarded, isLoggedIn, isSidebarCollapsed } = useAppContext();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Return null or a loading state during SSR/initial hydration to avoid mismatches
  if (!mounted) {
    return <div style={{ background: 'var(--background)', minHeight: '100vh' }} />;
  }

  if (!isOnboarded) {
    return <Welcome />;
  }

  if (!isLoggedIn) {
    return <Login />;
  }

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <main style={{ 
        marginLeft: isSidebarCollapsed ? '80px' : '260px', 
        width: isSidebarCollapsed ? 'calc(100vw - 80px)' : 'calc(100vw - 260px)', 
        minHeight: '100vh',
        padding: '40px',
        transition: 'all 0.3s ease-in-out'
      }}>
        {children}
      </main>
    </div>
  );
}
