"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaHome, FaHistory, FaCog, FaUser, FaSignOutAlt, FaTasks } from 'react-icons/fa';
import { useAppContext } from './AppContext';

const navItems = [
  { name: 'Home', icon: <FaHome />, overlay: null },
  { name: 'Conversations', icon: <FaHistory />, overlay: 'history' },
  { name: 'Tasks', icon: <FaTasks />, overlay: 'tasks' },
  { name: 'Settings', icon: <FaCog />, overlay: 'settings' },
  { name: 'Profile', icon: <FaUser />, overlay: 'profile' },
];

export default function Sidebar() {
  const { activeOverlay, setActiveOverlay, logout } = useAppContext();
  const [hoveredItem, setHoveredItem] = React.useState<string | null>(null);

  return (
    <div
      style={{
        position: 'fixed',
        left: '25px',
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 2000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '20px 10px',
        gap: '20px',
        width: '70px',
        borderRadius: '35px'
      }}
      className="glass-card"
    >
      <div style={{ 
        marginBottom: '10px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: 'var(--primary-gradient)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '12px',
          color: 'white',
          boxShadow: '0 5px 15px rgba(0,242,255,0.3)'
        }}>
          CX
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {navItems.map((item) => {
          const isActive = activeOverlay === item.overlay;
          return (
            <div key={item.name} style={{ position: 'relative' }}>
              <button
                onClick={() => setActiveOverlay(item.overlay as any)}
                onMouseEnter={() => setHoveredItem(item.name)}
                onMouseLeave={() => setHoveredItem(null)}
                style={{
                  width: '45px',
                  height: '45px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '15px',
                  color: isActive ? 'white' : 'var(--text-muted)',
                  background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
                  transition: 'all 0.3s',
                  fontSize: '20px',
                  border: isActive ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent',
                  cursor: 'pointer'
                }}
              >
                {item.icon}
              </button>

              <AnimatePresence>
                {hoveredItem === item.name && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    style={{
                      position: 'absolute',
                      left: '60px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'rgba(20, 20, 20, 0.95)',
                      backdropFilter: 'blur(15px)',
                      padding: '10px 20px',
                      borderRadius: '10px',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'white',
                      fontSize: '15px',
                      fontWeight: '700',
                      whiteSpace: 'nowrap',
                      pointerEvents: 'none',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.5)',
                      zIndex: 2001
                    }}
                  >
                    {item.name}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </nav>

      <div style={{ position: 'relative', marginTop: 'auto' }}>
        <button
          onClick={() => logout()}
          onMouseEnter={() => setHoveredItem('Logout')}
          onMouseLeave={() => setHoveredItem(null)}
          style={{
            width: '45px',
            height: '45px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '15px',
            color: 'var(--accent-primary)',
            transition: 'all 0.3s',
            fontSize: '20px',
            cursor: 'pointer'
          }}
        >
          <FaSignOutAlt />
        </button>

        <AnimatePresence>
          {hoveredItem === 'Logout' && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              style={{
                position: 'absolute',
                left: '60px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'rgba(20, 20, 20, 0.95)',
                backdropFilter: 'blur(15px)',
                padding: '10px 20px',
                borderRadius: '10px',
                border: '1px solid rgba(255,255,255,0.15)',
                color: 'var(--accent-primary)',
                fontSize: '15px',
                fontWeight: '700',
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                boxShadow: '0 8px 25px rgba(0,0,0,0.5)',
                zIndex: 2001
              }}
            >
              Logout
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
