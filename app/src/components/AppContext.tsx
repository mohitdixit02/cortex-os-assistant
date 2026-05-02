"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../utility/apiClient';

interface AppContextType {
  isOnboarded: boolean;
  setIsOnboarded: (val: boolean) => void;
  isLoggedIn: boolean;
  setIsLoggedIn: (val: boolean) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (val: boolean) => void;
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
  logout: () => void;
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
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
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
    updateActiveThreadId(null);
  };

  return (
    <AppContext.Provider value={{ 
      isOnboarded, 
      setIsOnboarded: updateOnboarded, 
      isLoggedIn, 
      setIsLoggedIn,
      isSidebarCollapsed,
      setIsSidebarCollapsed,
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
      logout
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
