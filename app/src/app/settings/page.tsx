"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { FaMicrophone, FaLanguage, FaToggleOn, FaToggleOff, FaHeadphones, FaSave, FaClock, FaGlobe } from 'react-icons/fa';
import { apiClient } from '../../utility/apiClient';
import { useAppContext } from '../../components/AppContext';
import { toast } from 'react-toastify';
import TimezoneSelect from 'react-timezone-select';

export default function Settings() {
  const { userConfig, refreshUserConfig } = useAppContext();

  if (!userConfig) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)' }}>
        Loading settings...
      </div>
    );
  }

  return (
    <SettingsForm 
      initialConfig={userConfig} 
      refreshUserConfig={refreshUserConfig} 
    />
  );
}

function SettingsForm({ initialConfig, refreshUserConfig }: { initialConfig: any, refreshUserConfig: () => Promise<void> }) {
  const { user, selectedMic, setSelectedMic, selectedSpeaker, setSelectedSpeaker } = useAppContext();

  const [voice, setVoice] = useState('en-US-Standard-C');
  const [language, setLanguage] = useState('English');

  // Local State initialized from props
  const [voiceClientTimeout, setVoiceClientTimeout] = useState(initialConfig.voice_client_timeout_seconds || 3);
  const [forceOpenWebsocket, setForceOpenWebsocket] = useState(initialConfig.force_open_websocket ?? true);
  const [reminderBeforeTriggerTime, setReminderBeforeTriggerTime] = useState(initialConfig.reminder_minutes_before_trigger_time || 0);
  const [timezone, setTimezone] = useState(initialConfig.timezone || 'UTC');
  const [timezoneMode, setTimezoneMode] = useState(initialConfig.timezone_mode || 'AUTO');
  const [isSaving, setIsSaving] = useState(false);

  // Track initial values to detect changes
  const initialValues = useRef(initialConfig);

  // Sync local state if the global config is refreshed
  useEffect(() => {
    setVoiceClientTimeout(initialConfig.voice_client_timeout_seconds || 3);
    setForceOpenWebsocket(initialConfig.force_open_websocket ?? true);
    setReminderBeforeTriggerTime(initialConfig.reminder_minutes_before_trigger_time || 0);
    setTimezone(initialConfig.timezone || 'UTC');
    setTimezoneMode(initialConfig.timezone_mode || 'AUTO');
    initialValues.current = initialConfig;
  }, [initialConfig]);

  const [micDevices, setMicDevices] = useState<MediaDeviceInfo[]>([]);
  const [speakerDevices, setSpeakerDevices] = useState<MediaDeviceInfo[]>([]);

  // Handle Automatic Timezone Detection (Locally for UI responsiveness)
  const handleTimezoneModeChange = (mode: string) => {
    setTimezoneMode(mode);
    if (mode === 'AUTO') {
      const detectedTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (detectedTz && detectedTz !== timezone) {
        setTimezone(detectedTz);
      }
    }
  };

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
    const userId = user?.id || user?.user_id;
    if (!userId) {
      toast.error("User not authenticated.");
      return;
    }

    const currentConfig = {
      voice_client_timeout_seconds: voiceClientTimeout,
      force_open_websocket: forceOpenWebsocket,
      reminder_minutes_before_trigger_time: reminderBeforeTriggerTime,
      timezone: timezone,
      timezone_mode: timezoneMode
    };

    // Check if anything has changed
    const isChanged = Object.keys(currentConfig).some(
      key => (currentConfig as any)[key] !== (initialValues.current as any)[key]
    );

    if (!isChanged) {
      toast.info("No changes detected.");
      return;
    }

    try {
      setIsSaving(true);
      await apiClient<any>(`/api/v1/user/config/${userId}`, {
        method: 'POST',
        body: JSON.stringify(currentConfig)
      });

      toast.success("Settings saved successfully!");
      await refreshUserConfig();
    } catch (err) {
      console.error("Failed to save user config", err);
      toast.error("Failed to save settings.");
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
          {/* Voice Interaction Section */}
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
                  onChange={(e) => setVoiceClientTimeout(parseInt(e.target.value) || 0)}
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
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Minutes to trigger before event time</div>
                </div>
                <input 
                  type="number"
                  value={reminderBeforeTriggerTime}
                  onChange={(e) => setReminderBeforeTriggerTime(parseInt(e.target.value) || 0)}
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
                  onChange={(e) => handleTimezoneModeChange(e.target.value)}
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
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '600' }}>Timezone</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>{timezoneMode === 'AUTO' ? 'Automatically detected' : 'Set your local timezone'}</div>
                </div>
                <div style={{ width: '350px' }}>
                  <TimezoneSelect
                    value={timezone}
                    isDisabled={timezoneMode === 'AUTO'}
                    onChange={(tz) => setTimezone(tz.value)}
                    menuPortalTarget={typeof window !== 'undefined' ? document.body : null}
                    styles={{
                      control: (base) => ({
                        ...base,
                        background: timezoneMode === 'AUTO' ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: 'white',
                        borderRadius: '8px',
                        cursor: timezoneMode === 'AUTO' ? 'not-allowed' : 'pointer',
                      }),
                      menuPortal: (base) => ({ ...base, zIndex: 9999 }),
                      menu: (base) => ({
                        ...base,
                        background: '#1a1a1a',
                        border: '1px solid rgba(255,255,255,0.1)',
                      }),
                      option: (base, { isFocused }) => ({
                        ...base,
                        background: isFocused ? 'rgba(255,255,255,0.05)' : 'transparent',
                        color: 'white',
                        cursor: 'pointer'
                      }),
                      singleValue: (base) => ({
                        ...base,
                        color: 'white'
                      }),
                      input: (base) => ({
                        ...base,
                        color: 'white'
                      })
                    }}
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Voice & Speech Section */}
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

          {/* Audio Devices Section */}
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
        </div>
      </motion.div>
    </div>
  );
}
