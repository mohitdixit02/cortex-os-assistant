"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';

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
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Load state from localStorage on mount ONLY
  useEffect(() => {
    setIsMounted(true);
    const onboarded = localStorage.getItem('isOnboarded') === 'true';
    const loggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const savedUser = localStorage.getItem('user');

    if (onboarded) setIsOnboarded(true);
    if (loggedIn) setIsLoggedIn(true);
    if (savedUser) setUser(JSON.parse(savedUser));
  }, []);

  const updateOnboarded = (val: boolean) => {
    setIsOnboarded(val);
    localStorage.setItem('isOnboarded', String(val));
  };

  const updateLoggedIn = (val: boolean) => {
    setIsLoggedIn(val);
    localStorage.setItem('isLoggedIn', String(val));
    if (!val) {
      setUser(null);
      localStorage.removeItem('user');
    }
  };

  const updateUser = (u: any) => {
    setUser(u);
    localStorage.setItem('user', JSON.stringify(u));
  };

  // Prevent hydration mismatch by not rendering children until mounted
  // or providing a consistent initial state. 
  // For this app, we'll provide the context and let components handle their own mounting if needed,
  // but standardizing the initial state to 'false' for SSR is key.

  return (
    <AppContext.Provider value={{ 
      isOnboarded, 
      setIsOnboarded: updateOnboarded, 
      isLoggedIn, 
      setIsLoggedIn: updateLoggedIn,
      isSidebarCollapsed,
      setIsSidebarCollapsed,
      user,
      setUser: updateUser
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
