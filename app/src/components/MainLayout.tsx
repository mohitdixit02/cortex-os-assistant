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
    <div style={{ 
      display: 'flex', 
      background: 'var(--background)',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden' 
    }}>
      {/* Sidebar - Persistent width container to prevent layout reflow during animation */}
      <div style={{ 
        width: isSidebarCollapsed ? '80px' : '260px', 
        transition: 'width 0.3s ease-in-out',
        flexShrink: 0,
        position: 'relative',
        zIndex: 100
      }}>
        <Sidebar />
      </div>
      
      {/* Main Content Area */}
      <div style={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <header style={{
          height: '70px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 40px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          background: 'rgba(10,10,10,0.6)',
          backdropFilter: 'blur(20px)',
          zIndex: 90,
          flexShrink: 0
        }}>
          <ThreadSelector />
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: '500', letterSpacing: '0.5px' }}>
            {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()}
          </div>
        </header>

        <main style={{ 
          flex: 1,
          overflow: 'hidden',
          background: 'var(--background)'
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
