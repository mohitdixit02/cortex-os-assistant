"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { signIn } from 'next-auth/react';
import { FcGoogle } from 'react-icons/fc';

export default function Login() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);
      // next-auth signIn for google
      await signIn('google');
    } catch (err: any) {
      setError("Failed to initiate Google login");
      setIsLoading(false);
    }
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
        
        {error && (
          <p style={{ color: '#ff4b2b', fontSize: '14px', marginBottom: '-10px' }}>{error}</p>
        )}

        <button 
          onClick={handleGoogleLogin}
          disabled={isLoading}
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
            transition: 'transform 0.2s',
            opacity: isLoading ? 0.7 : 1,
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
          onMouseDown={(e) => !isLoading && (e.currentTarget.style.transform = 'scale(0.98)')}
          onMouseUp={(e) => !isLoading && (e.currentTarget.style.transform = 'scale(1)')}
        >
          <FcGoogle size={24} />
          {isLoading ? "Connecting..." : "Sign in with Google"}
        </button>

        <p style={{ fontSize: '12px', color: '#555', marginTop: '10px' }}>
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </motion.div>
    </div>
  );
}
