"use client";

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from './AppContext';
import { FcGoogle } from 'react-icons/fc';
import { AssistantAPI } from './audio/AudioInterface';

const getAssistantApi = (): AssistantAPI | null => {
  if (typeof window === 'undefined') return null;
  return (window as Window & { assistantAPI?: AssistantAPI }).assistantAPI || null;
};

export default function Login() {
  const { setIsLoggedIn, setUser } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const api = getAssistantApi();
    if (!api) return;

    // Listen for auth redirect from Electron
    const cleanup = api.onAuthRedirect(async (url) => {
      try {
        setIsLoading(true);
        console.log("Received auth redirect:", url);
        
        // Extract the code from the URL (cortex-ai://auth?code=...)
        const urlObj = new URL(url);
        const code = urlObj.searchParams.get('code');
        
        if (code) {
          await handleBackendExchange(code);
        } else {
          throw new Error("No authorization code found in redirect URL");
        }
      } catch (err: any) {
        setError(err.message || "Authentication failed");
        setIsLoading(false);
      }
    });

    return cleanup;
  }, []);

  const handleBackendExchange = async (code: string) => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
    
    try {
      // NOTE: This is where the backend integration happens.
      // You will need to implement this endpoint on your backend.
      const response = await fetch(`${backendUrl}/api/auth/google/exchange`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, redirect_uri: "cortex-ai://auth" }),
      });

      if (!response.ok) {
        throw new Error("Failed to exchange code with backend");
      }

      const userData = await response.json();
      
      // Expected backend response: { name, email, image, token, ... }
      setUser(userData);
      setIsLoggedIn(true);
    } catch (err: any) {
      console.error("Exchange error:", err);
      // For now, if backend fails, we still allow demo login or show error
      setError("Backend exchange failed. Ensure your backend is running.");
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    const api = getAssistantApi();
    if (!api) return;

    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setError("Google Client ID not configured in .env");
      return;
    }

    const redirectUri = "cortex-ai://auth";
    const scope = encodeURIComponent("openid email profile");
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${scope}`;

    try {
      setIsLoading(true);
      setError(null);
      await api.openExternal(authUrl);
    } catch (err: any) {
      setError("Failed to open login window");
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
