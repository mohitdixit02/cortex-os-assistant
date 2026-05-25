"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { FaToggleOn, FaToggleOff, FaHeadphones, FaSave, FaClock, FaGlobe, FaSync, FaRobot, FaMicrophone, FaChevronDown } from 'react-icons/fa';
import { apiClient } from '../../utility/apiClient';
import { useAppContext } from '../../components/AppContext';
import { toast } from 'react-toastify';
import TimezoneSelect from 'react-timezone-select';
import { AnimatePresence } from 'framer-motion';

function CustomSelect({ 
  options, 
  value, 
  onChange, 
  width = '100%', 
  disabled = false 
}: { 
  options: { value: string, label: string }[], 
  value: string, 
  onChange: (val: string) => void,
  width?: string,
  disabled?: boolean
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find(o => o.value === value) || options[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const triggerStyle = {
    background: 'rgba(255,255,255,0.03)',
    color: disabled ? 'rgba(255,255,255,0.2)' : 'white',
    border: '1px solid rgba(255,255,255,0.08)',
    padding: '10px 15px',
    borderRadius: '12px',
    outline: 'none',
    transition: 'all 0.2s',
    cursor: disabled ? 'not-allowed' : 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: width,
    fontSize: '14px',
    fontWeight: '600'
  };

  return (
    <div ref={containerRef} style={{ position: 'relative', width }}>
      <button 
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)} 
        style={triggerStyle}
        onMouseEnter={(e) => {
          if (!disabled) {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
            e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
          }
        }}
        onMouseLeave={(e) => {
          if (!disabled) {
            e.currentTarget.style.borderColor = isOpen ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)';
            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
          }
        }}
      >
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {selectedOption?.label}
        </span>
        <FaChevronDown size={10} style={{ 
          opacity: 0.5, 
          transform: isOpen ? 'rotate(180deg)' : 'none',
          transition: 'transform 0.2s'
        }} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 5, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              background: 'rgba(15, 15, 15, 0.98)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              padding: '6px',
              zIndex: 1000,
              boxShadow: '0 15px 40px rgba(0,0,0,0.6)',
              maxHeight: '250px',
              overflowY: 'auto'
            }}
          >
            {options.map((opt, index) => (
              <div
                key={`${opt.value}-${index}`}
                onClick={() => {
                  onChange(opt.value);
                  setIsOpen(false);
                }}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  color: opt.value === value ? 'var(--accent-primary)' : 'white',
                  background: opt.value === value ? 'rgba(0,242,255,0.05)' : 'transparent',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  fontWeight: opt.value === value ? '700' : '400'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = opt.value === value ? 'rgba(0,242,255,0.08)' : 'rgba(255,255,255,0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = opt.value === value ? 'rgba(0,242,255,0.05)' : 'transparent';
                }}
              >
                {opt.label}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Settings() {
  const { userConfig, refreshUserConfig } = useAppContext();
  useEffect(() => {
    if (!userConfig) {
      refreshUserConfig();
    }
  }, [userConfig, refreshUserConfig]);

  if (!userConfig) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%', 
        color: 'var(--text-muted)',
        gap: '20px'
      }}>
        <div className="spin" style={{ fontSize: '24px' }}>
          <FaSync />
        </div>
        <span>Loading settings...</span>
        
        <style jsx>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .spin {
            animation: spin 1s linear infinite;
          }
        `}</style>
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

    // Apply strict 0-30 clamping before saving
    const finalTimeout = Math.min(30, Math.max(0, voiceClientTimeout));
    const finalBuffer = Math.min(30, Math.max(0, reminderBeforeTriggerTime));

    const currentConfig = {
      voice_client_timeout_seconds: finalTimeout,
      force_open_websocket: forceOpenWebsocket,
      reminder_minutes_before_trigger_time: finalBuffer,
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
      // Update local state if clamping happened
      setVoiceClientTimeout(finalTimeout);
      setReminderBeforeTriggerTime(finalBuffer);
      await refreshUserConfig();
    } catch (err) {
      console.error("Failed to save user config", err);
      toast.error("Failed to save settings.");
    } finally {
      setIsSaving(false);
    }
  };

  const inputStyle = {
    background: 'rgba(255,255,255,0.03)',
    color: 'white',
    border: '1px solid rgba(255,255,255,0.08)',
    padding: '10px 15px',
    borderRadius: '12px',
    outline: 'none',
    transition: 'all 0.2s',
    cursor: 'pointer',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
  };

  const selectStyle = {
    ...inputStyle,
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='rgba(255,255,255,0.5)' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 15px center',
    backgroundSize: '14px',
    paddingRight: '45px'
  };

  const onInputFocus = (e: any) => {
    e.target.style.borderColor = 'var(--accent-primary)';
    e.target.style.background = 'rgba(255,255,255,0.06)';
    e.target.style.boxShadow = '0 0 15px rgba(0,242,255,0.1)';
  };

  const onInputBlur = (e: any) => {
    e.target.style.borderColor = 'rgba(255,255,255,0.08)';
    e.target.style.background = 'rgba(255,255,255,0.03)';
    e.target.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
          <div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Assistant <span className="gradient-text">Settings</span></h1>
            <p style={{ color: 'var(--text-muted)' }}>Customize your Cortex experience based on your preferences.</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSaveConfigs}
            disabled={isSaving}
            className="btn-neon-purple-gradient"
            style={{
              padding: '12px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '15px',
              height: '48px',
              opacity: isSaving ? 0.7 : 1,
              boxShadow: '0 10px 20px rgba(255, 0, 229, 0.15)'
            }}
          >
            <FaSave /> {isSaving ? 'Saving...' : 'Save Configuration'}
          </motion.button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', paddingBottom: '40px' }}>
          {/* Cortex Interaction Section */}
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="icon-glass-container" style={{ width: '36px', height: '36px' }}>
                <FaRobot size={16} color="var(--accent-primary)" />
              </div>
              Cortex Interaction
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Wait Timeout</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>The amount of seconds Cortex should wait for voice input before responding. Cortex will wait in case it thought your speech or thought is not finished yet. Setting this to 0 will make Cortex respond immediately after it thinks you are done talking.
                  </div>
                </div>
                <input 
                  type="number"
                  min="0"
                  max="30"
                  value={voiceClientTimeout}
                  onChange={(e) => setVoiceClientTimeout(parseInt(e.target.value) || 0)}
                  onFocus={onInputFocus}
                  onBlur={(e) => {
                    onInputBlur(e);
                    const val = Math.min(30, Math.max(0, parseInt(e.target.value) || 0));
                    setVoiceClientTimeout(val);
                  }}
                  style={{ ...inputStyle, width: '90px', textAlign: 'center' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Force Audio Reminder</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                    If enabled, Cortex will turn on the conversation (in case it was off) and respond with audio for the reminder notification. If disabled, you will only get notification in case conversation is stopped.
                  </div>
                </div>
                <button 
                  onClick={() => setForceOpenWebsocket(!forceOpenWebsocket)}
                  style={{
                    fontSize: '36px',
                    color: forceOpenWebsocket ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                    background: 'none',
                    border: 'none',
                    transition: 'color 0.2s'
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
              <div className="icon-glass-container" style={{ width: '36px', height: '36px' }}>
                <FaClock size={16} color="var(--accent-secondary)" />
              </div>
              Scheduler Configs
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Reminder Buffer Time</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                    The amount of minutes before the actual requested time that Cortex should start reminding you about the event. Setting this to 0 will make Cortex remind you exactly at the time requested.
                  </div>
                </div>
                <input 
                  type="number"
                  min="0"
                  max="30"
                  value={reminderBeforeTriggerTime}
                  onChange={(e) => setReminderBeforeTriggerTime(parseInt(e.target.value) || 0)}
                  onFocus={onInputFocus}
                  onBlur={(e) => {
                    onInputBlur(e);
                    const val = Math.min(30, Math.max(0, parseInt(e.target.value) || 0));
                    setReminderBeforeTriggerTime(val);
                  }}
                  style={{ ...inputStyle, width: '90px', textAlign: 'center' }}
                />
              </div>
            </div>
          </section>

          {/* Regional Settings */}
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="icon-glass-container" style={{ width: '36px', height: '36px' }}>
                <FaGlobe size={16} color="var(--accent-primary)" />
              </div>
              Regional Settings
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Timezone Mode</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Automatic or Manual timezone detection</div>
                </div>
                <CustomSelect 
                  value={timezoneMode} 
                  onChange={(val) => handleTimezoneModeChange(val)}
                  options={[
                    { value: 'AUTO', label: 'AUTO' },
                    { value: 'MANUAL', label: 'MANUAL' }
                  ]}
                  width="140px"
                />
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
                      control: (base, state) => ({
                        ...base,
                        background: timezoneMode === 'AUTO' ? 'rgba(255,255,255,0.01)' : 'rgba(255,255,255,0.03)',
                        border: state.isFocused ? '1px solid var(--accent-primary)' : '1px solid rgba(255,255,255,0.08)',
                        color: 'white',
                        borderRadius: '12px',
                        cursor: timezoneMode === 'AUTO' ? 'not-allowed' : 'pointer',
                        boxShadow: 'none',
                        '&:hover': {
                          borderColor: state.isFocused ? 'var(--accent-primary)' : 'rgba(255,255,255,0.15)'
                        }
                      }),
                      menuPortal: (base) => ({ ...base, zIndex: 9999 }),
                      menu: (base) => ({
                        ...base,
                        background: '#0a0a0a',
                        border: '1px solid rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        boxShadow: '0 10px 40px rgba(0,0,0,0.8)'
                      }),
                      option: (base, { isFocused, isSelected }) => ({
                        ...base,
                        background: isSelected ? 'var(--accent-primary)' : isFocused ? 'rgba(255,255,255,0.05)' : 'transparent',
                        color: isSelected ? 'black' : 'white',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: isSelected ? '700' : '400',
                        '&:active': {
                          background: 'var(--accent-primary)'
                        }
                      }),
                      singleValue: (base) => ({
                        ...base,
                        color: 'white',
                        fontWeight: '600'
                      }),
                      input: (base) => ({
                        ...base,
                        color: 'white'
                      }),
                      dropdownIndicator: (base) => ({
                        ...base,
                        color: 'rgba(255,255,255,0.3)'
                      }),
                      indicatorSeparator: () => ({ display: 'none' })
                    }}
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Audio Devices Section */}
          <section className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="icon-glass-container" style={{ width: '36px', height: '36px' }}>
                <FaHeadphones size={16} color="var(--accent-secondary)" />
              </div>
              Audio Devices
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Microphone</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Select input device</div>
                </div>
                <CustomSelect 
                  value={selectedMic || 'default'} 
                  onChange={(val) => setSelectedMic(val)}
                  options={[
                    { value: 'default', label: 'System Default' },
                    ...micDevices.map(d => ({ value: d.label, label: d.label || `Device ${d.deviceId.slice(0, 5)}` }))
                  ]}
                  width="300px"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>Speaker</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Select output device</div>
                </div>
                <CustomSelect 
                  value={selectedSpeaker || 'default'} 
                  onChange={(val) => setSelectedSpeaker(val)}
                  options={[
                    { value: 'default', label: 'System Default' },
                    ...speakerDevices.map(d => ({ value: d.deviceId, label: d.label || `Device ${d.deviceId.slice(0, 5)}` }))
                  ]}
                  width="300px"
                />
              </div>
            </div>
          </section>
        </div>
      </motion.div>
    </div>
  );
}
