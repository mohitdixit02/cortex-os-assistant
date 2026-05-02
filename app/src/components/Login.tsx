"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FcGoogle } from 'react-icons/fc';
import { useAppContext } from './AppContext';
import { apiClient } from '../utility/apiClient';

declare global {
  interface Window {
    assistantAPI: any;
  }
}

export default function Login() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setToken, setUser } = useAppContext();

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const { url: authUrl } = await apiClient<{ url: string }>('/api/v1/auth/google/authorize');
      
      if (window.assistantAPI?.startAuthFlow) {
        const result = await window.assistantAPI.startAuthFlow(authUrl);
        
        if (result.error) {
          throw new Error(result.error);
        }

        if (result.url) {
          const urlObj = new URL(result.url);
          const code = urlObj.searchParams.get('code');
          const state = urlObj.searchParams.get('state');
          if (code) {
            const response = await apiClient<{ access_token: string; user_id: string }>(
              `/api/v1/auth/google/callback?code=${code}${state ? `&state=${state}` : ''}`,
              { method: 'POST' }
            );
            
            setToken(response.access_token);
            
            // Fetch real user info
            const userData = await apiClient<{ user_id: string, full_name: string, email: string, profile_picture?: string, phone_number?: string }>(
              '/api/v1/auth/me'
            );
            setUser({ 
              id: userData.user_id, 
              name: userData.full_name, 
              email: userData.email, 
              image: userData.profile_picture 
            }); 
          }
        }
      } else {
        // Fallback for browser testing if applicable
        window.location.href = authUrl;
      }
    } catch (err: any) {
      setError(err.message || "Failed to complete authentication");
      setIsLoading(false);
    } finally {
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
