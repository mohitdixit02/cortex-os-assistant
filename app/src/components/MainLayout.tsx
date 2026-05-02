"use client";

import React, { useEffect, useState } from 'react';
import { useAppContext } from './AppContext';
import Welcome from './Welcome';
import Login from './Login';
import Sidebar from './Sidebar';
import ThreadSelector from './ThreadSelector';

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
    <div style={{ display: 'flex', background: 'var(--background)' }}>
      <Sidebar />
      <div style={{ 
        marginLeft: isSidebarCollapsed ? '80px' : '260px', 
        width: isSidebarCollapsed ? 'calc(100vw - 80px)' : 'calc(100vw - 260px)', 
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease-in-out'
      }}>
        <header style={{
          height: '70px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 40px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          background: 'rgba(10,10,10,0.8)',
          backdropFilter: 'blur(10px)',
          position: 'sticky',
          top: 0,
          zIndex: 90
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <ThreadSelector />
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            {new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        </header>

        <main style={{ 
          flex: 1,
          padding: '40px',
          overflowY: 'auto'
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
