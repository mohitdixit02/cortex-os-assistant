"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FaMicrophone, FaLanguage, FaVolumeUp, FaMoon, FaCalendarAlt, FaToggleOn, FaToggleOff, FaHeadphones } from 'react-icons/fa';
import { apiClient } from '../../utility/apiClient';
import { useAppContext } from '../../components/AppContext';

export default function Settings() {
  const { 
    selectedMic, setSelectedMic, 
    selectedSpeaker, setSelectedSpeaker 
  } = useAppContext();

  const [voice, setVoice] = useState('en-US-Standard-C');
  const [language, setLanguage] = useState('English');
  const [volume, setVolume] = useState(80);
  const [calendarSubscribed, setCalendarSubscribed] = useState(false);
  const [isUpdatingCalendar, setIsUpdatingCalendar] = useState(false);

  const [micDevices, setMicDevices] = useState<MediaDeviceInfo[]>([]);
  const [speakerDevices, setSpeakerDevices] = useState<MediaDeviceInfo[]>([]);

  // Fetch initial tool subscription status
  useEffect(() => {
    async function fetchToolStatus() {
      try {
        const status = await apiClient<{ linked: boolean, token_valid: boolean }>('/api/v1/calendar/status');
        setCalendarSubscribed(status.linked);
      } catch (err) {
        console.error("Failed to fetch tool status", err);
      }
    }
    fetchToolStatus();
  }, []);

  // Fetch audio devices
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        // Trigger permission prompt if labels are empty
        const devicesBefore = await navigator.mediaDevices.enumerateDevices();
        if (devicesBefore.some(d => d.kind === 'audioinput' && !d.label)) {
          await navigator.mediaDevices.getUserMedia({ audio: true });
        }
        
        const allDevices = await navigator.mediaDevices.enumerateDevices();
        setMicDevices(allDevices.filter(d => d.kind === 'audioinput'));
        setSpeakerDevices(allDevices.filter(d => d.kind === 'audiooutput'));
      } catch (err) {
        console.error("Failed to fetch devices", err);
      }
    };
    fetchDevices();

    // Listen for device changes
    navigator.mediaDevices.ondevicechange = fetchDevices;
    return () => {
      navigator.mediaDevices.ondevicechange = null;
    };
  }, []);

  const toggleCalendar = async () => {
    try {
      setIsUpdatingCalendar(true);
      const newStatus = !calendarSubscribed;
      await apiClient(`/api/v1/user/tools/google_calendar/subscription`, {
        method: 'POST',
        body: JSON.stringify({ is_subscribed: newStatus })
      });
      setCalendarSubscribed(newStatus);
    } catch (err) {
      console.error("Failed to update calendar subscription", err);
    } finally {
      setIsUpdatingCalendar(false);
    }
  };

  return (
    <div style={{
      height: '100%',
      overflowY: 'auto',
      padding: '40px'
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ maxWidth: '95%', margin: '0 auto' }}
      >
        <div style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Assistant <span className="gradient-text">Settings</span></h1>
          <p style={{ color: 'var(--text-muted)' }}>Customize your Cortex experience to your liking.</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', paddingBottom: '40px' }}>
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaMicrophone color="var(--accent-primary)" /> Voice & Speech
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Assistant Voice</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Choose how Cortex sounds to you</div>
                </div>
                <select 
                  value={voice} 
                  onChange={(e) => setVoice(e.target.value)}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    outline: 'none',
                    cursor: 'pointer'
                  }}
                >
                  <option value="en-US-Standard-C">English (US) - Male</option>
                  <option value="en-US-Standard-E">English (US) - Female</option>
                  <option value="en-GB-Standard-A">English (UK) - Female</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Speech Language</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Preferred language for interaction</div>
                </div>
                <select 
                  value={language} 
                  onChange={(e) => setLanguage(e.target.value)}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    outline: 'none',
                    cursor: 'pointer'
                  }}
                >
                  <option value="English">English</option>
                  <option value="Spanish">Spanish</option>
                  <option value="French">French</option>
                  <option value="German">German</option>
                </select>
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaHeadphones color="var(--accent-secondary)" /> Audio Devices
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Microphone</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Select input device</div>
                </div>
                <select 
                  value={selectedMic || 'default'} 
                  onChange={(e) => setSelectedMic(e.target.value)}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    outline: 'none',
                    maxWidth: '300px',
                    cursor: 'pointer'
                  }}
                >
                  <option value="default">System Default</option>
                  {micDevices.map(device => (
                    <option key={device.deviceId} value={device.label}>{device.label || `Device ${device.deviceId.slice(0, 5)}`}</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Speaker</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Select output device</div>
                </div>
                <select 
                  value={selectedSpeaker || 'default'} 
                  onChange={(e) => setSelectedSpeaker(e.target.value)}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    outline: 'none',
                    maxWidth: '300px',
                    cursor: 'pointer'
                  }}
                >
                  <option value="default">System Default</option>
                  {speakerDevices.map(device => (
                    <option key={device.deviceId} value={device.deviceId}>{device.label || `Device ${device.deviceId.slice(0, 5)}`}</option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaCalendarAlt color="var(--accent-secondary)" /> Tools & Integrations
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Google Calendar API</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Allow Cortex to manage your schedule</div>
                </div>
                <button 
                  onClick={toggleCalendar}
                  disabled={isUpdatingCalendar}
                  style={{
                    fontSize: '32px',
                    color: calendarSubscribed ? 'var(--accent-secondary)' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    opacity: isUpdatingCalendar ? 0.5 : 1,
                    cursor: isUpdatingCalendar ? 'not-allowed' : 'pointer'
                  }}
                >
                  {calendarSubscribed ? <FaToggleOn /> : <FaToggleOff />}
                </button>
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaVolumeUp color="var(--accent-secondary)" /> Audio Output
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span style={{ fontWeight: '600' }}>Volume</span>
                  <span>{volume}%</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={volume} 
                  onChange={(e) => setVolume(parseInt(e.target.value))}
                  style={{
                    width: '100%',
                    accentColor: 'var(--accent-secondary)',
                    background: 'rgba(255,255,255,0.1)',
                    height: '6px',
                    borderRadius: '3px',
                    appearance: 'none',
                    outline: 'none',
                    cursor: 'pointer'
                  }}
                />
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaMoon color="var(--accent-primary)" /> Appearance
            </h2>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: '600' }}>Dark Mode</div>
                <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Currently enforced theme</div>
              </div>
              <div style={{
                width: '50px',
                height: '26px',
                background: 'var(--primary-gradient)',
                borderRadius: '13px',
                position: 'relative',
              }}>
                <div style={{
                  position: 'absolute',
                  right: '3px',
                  top: '3px',
                  width: '20px',
                  height: '20px',
                  background: 'white',
                  borderRadius: '50%'
                }} />
              </div>
            </div>
          </section>
        </div>
      </motion.div>
    </div>
  );
}
