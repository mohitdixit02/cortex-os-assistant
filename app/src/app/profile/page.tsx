"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from '../../components/AppContext';
import { FaEnvelope, FaChartBar, FaCalendarCheck, FaEdit } from 'react-icons/fa';

export default function Profile() {
  const { user } = useAppContext();

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
        <div style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Your <span className="gradient-text">Profile</span></h1>
            <p style={{ color: 'var(--text-muted)' }}>Manage your account and view your assistant usage.</p>
          </div>
          <button style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 20px',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.05)',
            color: 'white',
            border: '1px solid rgba(255,255,255,0.1)',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer'
          }}>
            <FaEdit /> Edit Profile
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          <section className="glass-card" style={{ padding: '30px', gridColumn: 'span 2', display: 'flex', alignItems: 'center', gap: '30px' }}>
            <img 
              src={user?.image || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || "Demo"}`} 
              alt="Profile" 
              style={{ width: '100px', height: '100px', borderRadius: '50%', border: '4px solid var(--accent-secondary)' }}
            />
            <div>
              <h2 style={{ fontSize: '24px', fontWeight: 'bold' }}>{user?.name || "User"}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginTop: '5px' }}>
                <FaEnvelope size={14} /> {user?.email || "No email available"}
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaChartBar color="var(--accent-secondary)" /> Usage Statistics
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Total Conversations</span>
                <span style={{ fontWeight: '600' }}>124</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Voice Interaction Time</span>
                <span style={{ fontWeight: '600' }}>12.5 hrs</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Tasks Completed</span>
                <span style={{ fontWeight: '600' }}>48</span>
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaCalendarCheck color="var(--accent-primary)" /> Recent Activity
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ fontSize: '14px' }}>
                <div style={{ fontWeight: '600' }}>Last Active</div>
                <div style={{ color: 'var(--text-muted)' }}>Today at 10:45 AM</div>
              </div>
              <div style={{ fontSize: '14px' }}>
                <div style={{ fontWeight: '600' }}>Account Created</div>
                <div style={{ color: 'var(--text-muted)' }}>March 15, 2026</div>
              </div>
            </div>
          </section>
        </div>
      </motion.div>
    </div>
  );
}
