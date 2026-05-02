"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter, usePathname } from 'next/navigation';
import { FaHome, FaHistory, FaCog, FaUser, FaSignOutAlt, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { useAppContext } from './AppContext';

const navItems = [
  { name: 'Home', icon: <FaHome />, path: '/' },
  { name: 'History', icon: <FaHistory />, path: '/history' },
  { name: 'Settings', icon: <FaCog />, path: '/settings' },
  { name: 'Profile', icon: <FaUser />, path: '/profile' },
];

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { isSidebarCollapsed, setIsSidebarCollapsed, logout } = useAppContext();

  return (
    <div
      style={{
        height: '100vh',
        background: 'var(--sidebar-bg)',
        borderRight: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        flexDirection: 'column',
        padding: isSidebarCollapsed ? '30px 10px' : '30px 20px',
        width: '100%', // Take full width of parent container
        overflow: 'hidden'
      }}
    >
      <div style={{ 
        marginBottom: '50px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: isSidebarCollapsed ? 'center' : 'space-between',
        paddingLeft: isSidebarCollapsed ? '0' : '10px' 
      }}>
        {!isSidebarCollapsed && (
          <motion.h2 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ 
              fontSize: '22px', 
              fontWeight: 'bold', 
              background: 'var(--primary-gradient)', 
              WebkitBackgroundClip: 'text', 
              WebkitTextFillColor: 'transparent',
              whiteSpace: 'nowrap'
            }}
          >
            Cortex
          </motion.h2>
        )}
        <button 
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          style={{
            color: 'var(--text-muted)',
            padding: '8px',
            borderRadius: '8px',
            background: 'rgba(255,255,255,0.03)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
        >
          {isSidebarCollapsed ? <FaChevronRight /> : <FaChevronLeft />}
        </button>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <button
              key={item.name}
              onClick={() => router.push(item.path)}
              title={isSidebarCollapsed ? item.name : ""}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '15px',
                padding: '12px',
                borderRadius: '12px',
                color: isActive ? 'white' : 'var(--text-muted)',
                background: isActive ? 'rgba(255,255,255,0.05)' : 'transparent',
                transition: 'all 0.2s',
                fontSize: '15px',
                fontWeight: isActive ? '600' : '400',
                border: isActive ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent',
                justifyContent: isSidebarCollapsed ? 'center' : 'flex-start',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                  e.currentTarget.style.color = 'white';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-muted)';
                }
              }}
            >
              <span style={{ fontSize: '18px', minWidth: '24px', display: 'flex', justifyContent: 'center' }}>
                {item.icon}
              </span>
              {!isSidebarCollapsed && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  {item.name}
                </motion.span>
              )}
            </button>
          );
        })}
      </nav>

      <button
        onClick={() => logout()}
        title={isSidebarCollapsed ? "Logout" : ""}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '15px',
          padding: '12px',
          borderRadius: '12px',
          color: 'var(--accent-primary)',
          transition: 'all 0.2s',
          fontSize: '15px',
          marginTop: 'auto',
          justifyContent: isSidebarCollapsed ? 'center' : 'flex-start',
          cursor: 'pointer'
        }}
        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(199,80,82,0.05)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
      >
        <FaSignOutAlt size={18} />
        {!isSidebarCollapsed && (
          <motion.span
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
          >
            Logout
          </motion.span>
        )}
      </button>
    </div>
  );
}
