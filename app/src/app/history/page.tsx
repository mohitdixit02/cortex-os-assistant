"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaHistory, FaCalendarAlt, FaChevronRight, FaTasks, FaCheckCircle, FaSpinner, FaTimesCircle } from 'react-icons/fa';
import { useThreads, useTasks } from '../../hooks/useApi';
import { useAppContext } from '../../components/AppContext';
import { useRouter } from 'next/navigation';

export default function History() {
  const [activeTab, setActiveTab] = useState<'conversations' | 'tasks'>('conversations');
  const { threads, isLoading: threadsLoading } = useThreads();
  const [taskPage, setTaskPage] = useState(1);
  const { tasks, isLoading: tasksLoading } = useTasks(taskPage);
  const { setActiveThreadId } = useAppContext();
  const router = useRouter();

  const handleThreadClick = (id: string) => {
    setActiveThreadId(id);
    router.push('/');
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <FaCheckCircle color="#10b981" />;
      case 'processing': return <FaSpinner className="spin" color="var(--accent-secondary)" />;
      case 'failed': return <FaTimesCircle color="var(--accent-primary)" />;
      default: return <FaHistory color="var(--text-muted)" />;
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
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Interaction <span className="gradient-text">History</span></h1>
          <p style={{ color: 'var(--text-muted)' }}>Review your past conversations and automated tasks performed by Cortex.</p>
        </div>

        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          marginBottom: '30px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          paddingBottom: '10px'
        }}>
          <button 
            onClick={() => setActiveTab('conversations')}
            style={{
              padding: '10px 20px',
              color: activeTab === 'conversations' ? 'white' : 'var(--text-muted)',
              fontWeight: '600',
              fontSize: '16px',
              position: 'relative',
              transition: 'color 0.2s'
            }}
          >
            Conversations
            {activeTab === 'conversations' && (
              <motion.div layoutId="tab-underline" style={{ position: 'absolute', bottom: '-11px', left: 0, right: 0, height: '2px', background: 'var(--accent-secondary)' }} />
            )}
          </button>
          <button 
            onClick={() => setActiveTab('tasks')}
            style={{
              padding: '10px 20px',
              color: activeTab === 'tasks' ? 'white' : 'var(--text-muted)',
              fontWeight: '600',
              fontSize: '16px',
              position: 'relative',
              transition: 'color 0.2s'
            }}
          >
            Automated Tasks
            {activeTab === 'tasks' && (
              <motion.div layoutId="tab-underline" style={{ position: 'absolute', bottom: '-11px', left: 0, right: 0, height: '2px', background: 'var(--accent-secondary)' }} />
            )}
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'conversations' ? (
            <motion.div
              key="conversations"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}
            >
              {threadsLoading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading conversations...</div>
              ) : threads?.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No conversations yet.</div>
              ) : threads?.map((thread, index) => (
                <motion.div
                  key={thread.session_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass-card"
                  onClick={() => handleThreadClick(thread.session_id)}
                  style={{
                    padding: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <div style={{ 
                      width: '45px', 
                      height: '45px', 
                      borderRadius: '12px', 
                      background: 'var(--primary-gradient)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      fontSize: '16px'
                    }}>
                      <FaHistory color="white" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>{thread.summary || "New Conversation"}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <FaCalendarAlt size={12} /> {new Date(thread.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <FaChevronRight color="var(--text-muted)" />
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="tasks"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}
            >
              {tasksLoading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading tasks...</div>
              ) : tasks?.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No tasks recorded yet.</div>
              ) : (
                <>
                  {tasks?.map((task, index) => (
                    <motion.div
                      key={task.task_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="glass-card"
                      style={{
                        padding: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        transition: 'background 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flex: 1 }}>
                        <div style={{ 
                          width: '50px', 
                          height: '50px', 
                          borderRadius: '12px', 
                          background: 'rgba(255,255,255,0.05)', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center',
                          fontSize: '16px',
                          border: '1px solid rgba(255,255,255,0.1)'
                        }}>
                          <FaTasks color="var(--accent-secondary)" />
                        </div>
                        <div style={{ flex: 1 }}>
                          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>{task.task_name}</h3>
                          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px', maxWidth: '500px' }}>{task.task_description}</p>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '15px', fontSize: '10px' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                              <FaCalendarAlt size={10} /> {new Date(task.created_at).toLocaleString()}
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'white', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                              {getStatusIcon(task.status)} {task.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '20px' }}>
                    <button 
                      disabled={taskPage === 1}
                      onClick={() => setTaskPage(p => p - 1)}
                      style={{ 
                        padding: '8px 16px', 
                        borderRadius: '8px', 
                        background: 'rgba(255,255,255,0.05)', 
                        color: 'white', 
                        opacity: taskPage === 1 ? 0.5 : 1,
                        cursor: taskPage === 1 ? 'not-allowed' : 'pointer'
                      }}
                    >
                      Previous
                    </button>
                    <div style={{ display: 'flex', alignItems: 'center', color: 'white' }}>Page {taskPage}</div>
                    <button 
                      disabled={tasks && tasks.length < 20}
                      onClick={() => setTaskPage(p => p + 1)}
                      style={{ 
                        padding: '8px 16px', 
                        borderRadius: '8px', 
                        background: 'rgba(255,255,255,0.05)', 
                        color: 'white', 
                        opacity: (tasks && tasks.length < 20) ? 0.5 : 1,
                        cursor: (tasks && tasks.length < 20) ? 'not-allowed' : 'pointer'
                      }}
                    >
                      Next
                    </button>
                  </div>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <style jsx global>{`
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
