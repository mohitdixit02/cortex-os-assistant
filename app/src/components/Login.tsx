"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from './AppContext';
import { FcGoogle } from 'react-icons/fc';

export default function Login() {
  const { setIsLoggedIn, setUser } = useAppContext();

  const handleLogin = () => {
    // Mock Google Login
    const mockUser = {
      name: "Demo User",
      email: "demo@example.com",
      image: "https://api.dicebear.com/7.x/avataaars/svg?seed=Demo"
    };
    setUser(mockUser);
    setIsLoggedIn(true);
  };

  return (
    <div style={{
      height: '100vh',
      width: '100vw',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--background)'
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        style={{
          width: '350px',
          padding: '40px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px'
        }}
        className="glass-card"
      >
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', background: 'var(--primary-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Cortex AI</h2>
        <p style={{ color: 'var(--text-muted)' }}>Sign in to continue to your assistant</p>
        
        <button 
          onClick={handleLogin}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            padding: '14px',
            borderRadius: '12px',
            background: 'white',
            color: '#1f1f1f',
            fontWeight: '600',
            fontSize: '16px',
            border: '1px solid #ddd',
            transition: 'transform 0.2s'
          }}
          onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
          onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <FcGoogle size={24} />
          Sign in with Google
        </button>

        <p style={{ fontSize: '12px', color: '#555', marginTop: '10px' }}>
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </motion.div>
    </div>
  );
}
