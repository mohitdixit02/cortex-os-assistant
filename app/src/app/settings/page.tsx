"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FaMicrophone, FaLanguage, FaVolumeUp, FaMoon, FaCalendarAlt, FaToggleOn, FaToggleOff, FaHeadphones, FaSave, FaClock, FaGlobe } from 'react-icons/fa';
import { apiClient } from '../../utility/apiClient';
import { useAppContext } from '../../components/AppContext';

export default function Settings() {
  const { 
    user,
    selectedMic, setSelectedMic, 
    selectedSpeaker, setSelectedSpeaker 
  } = useAppContext();

  const [voice, setVoice] = useState('en-US-Standard-C');
  const [language, setLanguage] = useState('English');
  const [volume, setVolume] = useState(80);

  // User Config State
  const [voiceClientTimeout, setVoiceClientTimeout] = useState(3);
  const [forceOpenWebsocket, setForceOpenWebsocket] = useState(true);
  const [reminderBeforeTriggerTime, setReminderBeforeTriggerTime] = useState(0);
  const [timezone, setTimezone] = useState('UTC');
  const [timezoneMode, setTimezoneMode] = useState('AUTO');
  const [isSaving, setIsSaving] = useState(false);

  const [micDevices, setMicDevices] = useState<MediaDeviceInfo[]>([]);
  const [speakerDevices, setSpeakerDevices] = useState<MediaDeviceInfo[]>([]);

  // Fetch User Config
  useEffect(() => {
    async function fetchUserConfig() {
      if (!user?.user_id) return;
      try {
        const config = await apiClient<any>(`/api/v1/user/config/${user.user_id}`);
        if (config) {
          setVoiceClientTimeout(config.voice_client_timeout);
          setForceOpenWebsocket(config.force_open_websocket);
          setReminderBeforeTriggerTime(config.reminder_before_trigger_time);
          setTimezone(config.timezone);
          setTimezoneMode(config.timezone_mode);
        }
      } catch (err) {
        console.error("Failed to fetch user config", err);
      }
    }
    fetchUserConfig();
  }, [user]);

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

  const handleSaveConfigs = async () => {
    if (!user?.user_id) return;
    try {
      setIsSaving(true);
      await apiClient(`/api/v1/user/config/${user.user_id}`, {
        method: 'POST',
        body: JSON.stringify({
          voice_client_timeout: voiceClientTimeout,
          force_open_websocket: forceOpenWebsocket,
          reminder_before_trigger_time: reminderBeforeTriggerTime,
          timezone: timezone,
          timezone_mode: timezoneMode
        })
      });
      alert("Settings saved successfully!");
    } catch (err) {
      console.error("Failed to save user config", err);
      alert("Failed to save settings.");
    } finally {
      setIsSaving(false);
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '40px' }}>
          <div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Assistant <span className="gradient-text">Settings</span></h1>
            <p style={{ color: 'var(--text-muted)' }}>Customize your Cortex experience to your liking.</p>
          </div>
          <button
            onClick={handleSaveConfigs}
            disabled={isSaving}
            className="action-button"
            style={{
              padding: '12px 25px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '16px',
              opacity: isSaving ? 0.7 : 1
            }}
          >
            <FaSave /> {isSaving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', paddingBottom: '40px' }}>
          {/* Voice Client Settings */}
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaMicrophone color="var(--accent-primary)" /> Voice Interaction
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Voice Client Timeout</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Seconds of silence before processing speech</div>
                </div>
                <input 
                  type="number"
                  value={voiceClientTimeout}
                  onChange={(e) => setVoiceClientTimeout(parseInt(e.target.value))}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    width: '80px',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Force Open WebSocket</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Allow proactive voice delivery from server</div>
                </div>
                <button 
                  onClick={() => setForceOpenWebsocket(!forceOpenWebsocket)}
                  style={{
                    fontSize: '32px',
                    color: forceOpenWebsocket ? 'var(--accent-secondary)' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                    background: 'none',
                    border: 'none'
                  }}
                >
                  {forceOpenWebsocket ? <FaToggleOn /> : <FaToggleOff />}
                </button>
              </div>
            </div>
          </section>

          {/* Scheduler Settings */}
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaClock color="var(--accent-secondary)" /> Scheduler Configs
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Reminder Buffer Time</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Seconds to trigger before event time</div>
                </div>
                <input 
                  type="number"
                  value={reminderBeforeTriggerTime}
                  onChange={(e) => setReminderBeforeTriggerTime(parseInt(e.target.value))}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    width: '80px',
                    outline: 'none'
                  }}
                />
              </div>
            </div>
          </section>

          {/* Regional Settings */}
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaGlobe color="var(--accent-primary)" /> Regional Settings
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Timezone Mode</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Automatic or Manual timezone detection</div>
                </div>
                <select 
                  value={timezoneMode} 
                  onChange={(e) => setTimezoneMode(e.target.value)}
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
                  <option value="AUTO">AUTO</option>
                  <option value="MANUAL">MANUAL</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Timezone</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Set your local timezone</div>
                </div>
                <input 
                  type="text"
                  value={timezone}
                  disabled={timezoneMode === 'AUTO'}
                  onChange={(e) => setTimezone(e.target.value)}
                  placeholder="e.g. UTC, Asia/Kolkata"
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.1)',
                    padding: '8px 15px',
                    borderRadius: '8px',
                    width: '200px',
                    outline: 'none',
                    opacity: timezoneMode === 'AUTO' ? 0.5 : 1
                  }}
                />
              </div>
            </div>
          </section>

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
