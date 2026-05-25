"use client";

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from '../../components/AppContext';
import { FaEnvelope, FaChartBar, FaCalendarCheck, FaGlobe } from 'react-icons/fa';
import Image from 'next/image';
import { apiClient } from '../../utility/apiClient';

const DEFAULT_IMG_URL = "https://images.icon-icons.com/1378/PNG/512/avatardefault_92824.png";

interface Stats {
  total_sessions: number;
  total_reminders: number;
  upcoming_reminders: number;
}

export default function Profile() {
  const { user, userConfig, refreshUserConfig, setUser } = useAppContext();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Refresh User Info (for created_at)
      const userData = await apiClient<any>('/api/v1/auth/me');
      setUser({
        id: userData.user_id,
        name: userData.full_name,
        email: userData.email,
        image: userData.profile_picture,
        created_at: userData.created_at
      });

      // Refresh Stats
      const statsData = await apiClient<Stats>('/api/v1/auth/stats');
      setStats(statsData);

      // Refresh Config (for timezone)
      await refreshUserConfig();
    } catch (err) {
      console.error("Failed to fetch profile data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatDate = (dateString: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
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
        <div style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Your <span className="gradient-text">Profile</span></h1>
            <p style={{ color: 'var(--text-muted)' }}>View your account details and assistant usage statistics.</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          <section className="glass-card" style={{ padding: '30px', gridColumn: 'span 2', display: 'flex', alignItems: 'center', gap: '30px' }}>
            <div style={{ position: 'relative', width: '100px', height: '100px' }}>
              <Image
                src={user?.image || DEFAULT_IMG_URL}
                alt="Profile"
                fill
                style={{ borderRadius: '50%', border: '3px solid var(--accent-primary)', objectFit: 'cover' }}
              />
            </div>
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
                <span style={{ color: 'var(--text-muted)' }}>Total Sessions</span>
                <span style={{ fontWeight: '600' }}>{loading ? "..." : stats?.total_sessions ?? 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Total Reminders Created</span>
                <span style={{ fontWeight: '600' }}>{loading ? "..." : stats?.total_reminders ?? 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Total Upcoming Reminders</span>
                <span style={{ fontWeight: '600' }}>{loading ? "..." : stats?.upcoming_reminders ?? 0}</span>
              </div>
            </div>
          </section>

          <section className="glass-card" style={{ padding: '30px' }}>
            <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaGlobe color="var(--accent-primary)" /> General Information
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Account Created</span>
                <span style={{ fontWeight: '600' }}>{loading ? "..." : formatDate(user?.created_at)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Is Active</span>
                <span style={{ fontWeight: '600', color: '#4caf50' }}>True</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Timezone</span>
                <span style={{ fontWeight: '600' }}>{loading ? "..." : userConfig?.timezone || "UTC"}</span>
              </div>
            </div>
          </section>
        </div>
      </motion.div>
      <div style={{ display: "flex", justifyContent: "center", "paddingTop": "30px", color: "rgb(134, 134, 134)" }}>
        @Cortex AI | {new Date().getFullYear()}
      </div>
    </div>
  );
}
