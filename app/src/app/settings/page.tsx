"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FaMicrophone, FaLanguage, FaVolumeUp, FaMoon, FaBell } from 'react-icons/fa';

export default function Settings() {
  const [voice, setVoice] = useState('en-US-Standard-C');
  const [language, setLanguage] = useState('English');
  const [volume, setVolume] = useState(80);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ maxWidth: '800px', margin: '0 auto' }}
    >
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Assistant <span className="gradient-text">Settings</span></h1>
        <p style={{ color: 'var(--text-muted)' }}>Customize your Cortex experience to your liking.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
        <section className="glass-card" style={{ padding: '30px' }}>
          <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FaMicrophone color="var(--accent-purple)" /> Voice & Speech
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
                  outline: 'none'
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
                  outline: 'none'
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
            <FaVolumeUp color="var(--accent-blue)" /> Audio Output
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
                  accentColor: 'var(--accent-blue)',
                  background: 'rgba(255,255,255,0.1)',
                  height: '6px',
                  borderRadius: '3px',
                  appearance: 'none',
                  outline: 'none'
                }}
              />
            </div>
          </div>
        </section>

        <section className="glass-card" style={{ padding: '30px' }}>
          <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FaMoon color="var(--accent-red)" /> Appearance
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
              cursor: 'pointer'
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
  );
}
