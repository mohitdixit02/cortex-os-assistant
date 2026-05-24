"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../utility/apiClient';
import { toast } from 'react-toastify';

interface AppContextType {
  isOnboarded: boolean;
  setIsOnboarded: (val: boolean) => void;
  isLoggedIn: boolean;
  setIsLoggedIn: (val: boolean) => void;
  activeOverlay: 'history' | 'tasks' | 'settings' | 'profile' | null;
  setActiveOverlay: (val: 'history' | 'tasks' | 'settings' | 'profile' | null) => void;
  user: any;
  setUser: (user: any) => void;
  token: string | null;
  setToken: (token: string | null) => void;
  activeThreadId: string | null;
  setActiveThreadId: (id: string | null) => void;
  selectedMic: string | null;
  setSelectedMic: (label: string | null) => void;
  selectedSpeaker: string | null;
  setSelectedSpeaker: (id: string | null) => void;
  userConfig: any;
  setUserConfig: (config: any) => void;
  refreshUserConfig: () => Promise<void>;
  logout: () => void;
  isConversationActive: boolean;
  setIsConversationActive: (val: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  // Initialize from localStorage safely
  const [isOnboarded, setIsOnboarded] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('isOnboarded') === 'true';
    }
    return false;
  });

  const [token, setTokenState] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  });

  const [user, setUserState] = useState<any>(() => {
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('user');
      return savedUser ? JSON.parse(savedUser) : null;
    }
    return null;
  });

  const [isLoggedIn, setIsLoggedIn] = useState(!!token);
  const [activeOverlay, setActiveOverlay] = useState<'history' | 'tasks' | 'settings' | 'profile' | null>(null);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('activeThreadId');
    }
    return null;
  });

  const [selectedMic, setSelectedMicState] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('selectedMic');
    }
    return null;
  });

  const [selectedSpeaker, setSelectedSpeakerState] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('selectedSpeaker');
    }
    return null;
  });

  const [isConversationActive, setIsConversationActive] = useState(false);

  const setToken = (newToken: string | null) => {
    setTokenState(newToken);
    if (typeof window !== 'undefined') {
      if (newToken) {
        localStorage.setItem('token', newToken);
        setIsLoggedIn(true);
      } else {
        localStorage.removeItem('token');
        setIsLoggedIn(false);
      }
    }
  };

  const setUser = (newUser: any) => {
    setUserState(newUser);
    if (typeof window !== 'undefined') {
      if (newUser) {
        localStorage.setItem('user', JSON.stringify(newUser));
      } else {
        localStorage.removeItem('user');
      }
    }
  };

  const updateActiveThreadId = (id: string | null) => {
    setActiveThreadId(id);
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem('activeThreadId', id);
      } else {
        localStorage.removeItem('activeThreadId');
      }
    }
  };

  const setSelectedMic = (label: string | null) => {
    setSelectedMicState(label);
    if (typeof window !== 'undefined') {
      if (label) {
        localStorage.setItem('selectedMic', label);
      } else {
        localStorage.removeItem('selectedMic');
      }
    }
  };

  const setSelectedSpeaker = (id: string | null) => {
    setSelectedSpeakerState(id);
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem('selectedSpeaker', id);
      } else {
        localStorage.removeItem('selectedSpeaker');
      }
    }
  };

  const updateOnboarded = (val: boolean) => {
    setIsOnboarded(val);
    if (typeof window !== 'undefined') {
      localStorage.setItem('isOnboarded', String(val));
    }
  };

  const [userConfig, setUserConfig] = useState<any>(null);

  const refreshUserConfig = React.useCallback(async () => {
    const userId = user?.id || user?.user_id;
    if (!isLoggedIn || !userId) return;

    try {
      let config = await apiClient<any>(`/api/v1/user/config/${userId}`);

      // Automatic Timezone Sync - Handle before setting state to avoid double render
      if (config?.timezone_mode === 'AUTO') {
        const detectedTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (detectedTz && detectedTz !== config.timezone) {
          console.log(`Timezone mismatch detected. Syncing ${detectedTz}...`);
          try {
            const updated = await apiClient<any>(`/api/v1/user/config/${userId}`, {
              method: 'POST',
              body: JSON.stringify({
                timezone: detectedTz
              })
            });
            
            if (updated && updated.config) {
              config = updated.config;
            } else {
              config = { ...config, timezone: detectedTz };
            }
            toast.info(`Timezone automatically updated to ${detectedTz}`);
          } catch (syncErr) {
            console.error("Failed to sync timezone automatically", syncErr);
          }
        }
      }
      
      setUserConfig(config);
    } catch (err) {
      console.error("Failed to sync global user config", err);
    }
  }, [isLoggedIn, user]);

  // Global Timezone & Config Sync
  useEffect(() => {
    let mounted = true;
    if (isLoggedIn && user) {
      refreshUserConfig();
    }
    return () => { mounted = false; };
  }, [isLoggedIn, user, refreshUserConfig]);

  const logout = async () => {
    try {
      if (token) {
        await apiClient('/api/v1/auth/logout', { method: 'POST' });
      }
    } catch (err) {
      console.error("Backend logout failed", err);
    }
    setToken(null);
    setUser(null);
    setUserConfig(null);
    updateActiveThreadId(null);
  };

  return (
    <AppContext.Provider value={{ 
      isOnboarded, 
      setIsOnboarded: updateOnboarded, 
      isLoggedIn, 
      setIsLoggedIn,
      activeOverlay,
      setActiveOverlay,
      user,
      setUser,
      token,
      setToken,
      activeThreadId,
      setActiveThreadId: updateActiveThreadId,
      selectedMic,
      setSelectedMic,
      selectedSpeaker,
      setSelectedSpeaker,
      logout,
      userConfig,
      setUserConfig,
      refreshUserConfig,
      isConversationActive,
      setIsConversationActive
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}
