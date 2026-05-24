"use client";

import React, { useEffect, useState } from 'react';
import { useAppContext } from './AppContext';
import Welcome from './Welcome';
import Login from './Login';
import Sidebar from './Sidebar';
import Conversations from '../app/history/page';
import Tasks from '../app/tasks/page';
import Settings from '../app/settings/page';
import Profile from '../app/profile/page';
import { motion, AnimatePresence } from 'framer-motion';
import { FaTimes } from 'react-icons/fa';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const { isOnboarded, isLoggedIn, activeOverlay, setActiveOverlay } = useAppContext();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close overlay on ESC key
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setActiveOverlay(null);
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [setActiveOverlay]);

  if (!mounted) {
    return <div style={{ background: 'var(--background)', minHeight: '100vh' }} />;
  }

  if (!isOnboarded) {
    return <Welcome />;
  }

  if (!isLoggedIn) {
    return <Login />;
  }

  const renderOverlayContent = () => {
    switch (activeOverlay) {
      case 'history': return <Conversations />;
      case 'tasks': return <Tasks />;
      case 'settings': return <Settings />;
      case 'profile': return <Profile />;
      default: return null;
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      background: 'var(--background)',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Global Navigation Dock */}
      <Sidebar />

      {/* Main Content Area */}
      <main style={{ 
        flex: 1,
        overflow: 'hidden',
        background: 'var(--background)',
        position: 'relative',
        paddingLeft: '110px'
      }}>
        {children}
      </main>

      {/* Glass Overlay System */}
      <AnimatePresence>
        {activeOverlay && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px',
              background: 'rgba(8, 8, 18, 0.73)',
              backdropFilter: 'blur(8px)'
            }}
          >
            {/* Clickable Backdrop to close */}
            <div 
              style={{ position: 'absolute', inset: 0 }} 
              onClick={() => setActiveOverlay(null)} 
            />

            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="glass-card"
              style={{
                width: '100%',
                maxWidth: '900px',
                maxHeight: '80vh',
                position: 'relative',
                zIndex: 1001,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
                border: '1px solid rgba(255,255,255,0.1)'
              }}
            >
              {/* Overlay Header */}
              <div style={{
                padding: '20px 30px',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(70, 70, 70, 0.19)'
              }}>
                <span style={{ 
                  fontSize: '18px', 
                  fontWeight: '700', 
                  textTransform: 'uppercase', 
                  letterSpacing: '1px',
                  color: 'var(--text-muted)'
                }}>
                  {activeOverlay}
                </span>
                <button 
                  onClick={() => setActiveOverlay(null)}
                  style={{
                    color: 'white',
                    padding: '8px',
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.05)',
                    display: 'flex',
                    cursor: 'pointer'
                  }}
                >
                  <FaTimes size={16} />
                </button>
              </div>

              {/* Overlay Scrollable Content */}
              <div style={{ flex: 1, overflowY: 'auto' }}>
                {renderOverlayContent()}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
