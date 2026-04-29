"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface AppContextType {
  isOnboarded: boolean;
  setIsOnboarded: (val: boolean) => void;
  isLoggedIn: boolean;
  setIsLoggedIn: (val: boolean) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (val: boolean) => void;
  user: any;
  setUser: (user: any) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  
  // Initialize from localStorage safely
  const [isOnboarded, setIsOnboarded] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('isOnboarded') === 'true';
    }
    return false;
  });

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [user, setUser] = useState<any>(null);

  // Sync with NextAuth session
  useEffect(() => {
    if (status === 'authenticated' && session?.user) {
      setIsLoggedIn(true);
      setUser(session.user);
    } else if (status === 'unauthenticated') {
      setIsLoggedIn(false);
      setUser(null);
    }
  }, [session, status]);

  const updateOnboarded = (val: boolean) => {
    setIsOnboarded(val);
    if (typeof window !== 'undefined') {
      localStorage.setItem('isOnboarded', String(val));
    }
  };

  return (
    <AppContext.Provider value={{ 
      isOnboarded, 
      setIsOnboarded: updateOnboarded, 
      isLoggedIn, 
      setIsLoggedIn, // Still provided but mainly driven by session
      isSidebarCollapsed,
      setIsSidebarCollapsed,
      user,
      setUser
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
