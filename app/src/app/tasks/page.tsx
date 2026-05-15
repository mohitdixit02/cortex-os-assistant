"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaCalendarAlt, FaTasks, FaCheckCircle, FaSpinner, FaTimesCircle, FaHistory } from 'react-icons/fa';
import { useTasks } from '../../hooks/useApi';

export default function Tasks() {
  const [taskPage, setTaskPage] = useState(1);
  const { tasks, isLoading: tasksLoading } = useTasks(taskPage);

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
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Automated <span className="gradient-text">Tasks</span></h1>
          <p style={{ color: 'var(--text-muted)' }}>Review the automated background tasks performed by Cortex.</p>
        </div>

        <AnimatePresence mode="wait">
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
