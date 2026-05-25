"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaCalendarAlt, FaTasks, FaCheckCircle, FaSpinner, FaTimesCircle, FaHistory, FaBell, FaClock } from 'react-icons/fa';
import { useTasks, useEvents } from '../../hooks/useApi';
import { ToolBadge } from '../../utility/toolConfig';
import { useAppContext } from '../../components/AppContext';

export default function Tasks() {
  const { activeThreadId } = useAppContext();
  const [activeTab, setActiveTab] = useState<'automated' | 'reminders'>('automated');
  const [taskPage, setTaskPage] = useState(1);
  const [eventPage, setEventPage] = useState(1);

  const { tasks, isLoading: tasksLoading } = useTasks(taskPage, 8, activeThreadId);
  const { events, isLoading: eventsLoading } = useEvents(eventPage, 8, activeThreadId);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'done':
        return <FaCheckCircle color="#10b981" />;
      case 'processing':
      case 'queued':
        return <FaSpinner className="spin" color="var(--accent-secondary)" />;
      case 'created':
        return <FaClock color="var(--accent-secondary)" />;
      case 'failed': return <FaTimesCircle color="var(--accent-primary)" />;
      default: return <FaHistory color="var(--text-muted)" />;
    }
  };

  const renderAutomatedTasks = () => (
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
                    <div style={{ marginTop: '-8px' }}>
                      <ToolBadge tool_id={task.tool_id} />
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {/* Pagination Controls */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '15px', 
            marginTop: '30px',
            padding: '10px'
          }}>
            <button 
              disabled={taskPage === 1}
              onClick={() => {
                setTaskPage(p => p - 1);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="btn-glass"
              style={{ 
                padding: '10px 20px', 
                borderRadius: '10px', 
                background: taskPage === 1 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)', 
                color: taskPage === 1 ? 'rgba(255,255,255,0.2)' : 'white', 
                cursor: taskPage === 1 ? 'not-allowed' : 'pointer',
                border: '1px solid rgba(255,255,255,0.1)',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>←</span> Previous
            </button>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              color: 'white',
              fontWeight: 'bold',
              boxShadow: '0 0 15px rgba(255,255,255,0.05)',
              fontSize: '14px'
            }}>
              {taskPage}
            </div>

            <button 
              disabled={tasks && tasks.length < 8}
              onClick={() => {
                setTaskPage(p => p + 1);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="btn-glass"
              style={{ 
                padding: '10px 20px', 
                borderRadius: '10px', 
                background: (tasks && tasks.length < 8) ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)', 
                color: (tasks && tasks.length < 8) ? 'rgba(255,255,255,0.2)' : 'white', 
                cursor: (tasks && tasks.length < 8) ? 'not-allowed' : 'pointer',
                border: '1px solid rgba(255,255,255,0.1)',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              Next <span>→</span>
            </button>
          </div>
          </>
          )}    </motion.div>
  );

  const renderReminders = () => (
    <motion.div
      key="events"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}
    >
      {eventsLoading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading reminders...</div>
      ) : events?.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No reminders set yet.</div>
      ) : (
        <>
          {events?.map((event, index) => (
            <motion.div
              key={event.id}
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
                  <FaBell color="var(--accent-primary)" />
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>{event.name}</h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px', maxWidth: '500px' }}>{event.event_description}</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px', fontSize: '10px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--accent-primary)', fontWeight: 'bold' }}>
                      <FaClock size={10} /> Trigger: {new Date(event.trigger_time).toLocaleString()}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                      Created: {new Date(event.created_at).toLocaleString()}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'white', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                      {getStatusIcon(event.status)} {event.status}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {/* Pagination Controls */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '15px', 
            marginTop: '30px',
            padding: '10px'
          }}>
            <button 
              disabled={eventPage === 1}
              onClick={() => {
                setEventPage(p => p - 1);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="btn-glass"
              style={{ 
                padding: '10px 20px', 
                borderRadius: '10px', 
                background: eventPage === 1 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)', 
                color: eventPage === 1 ? 'rgba(255,255,255,0.2)' : 'white', 
                cursor: eventPage === 1 ? 'not-allowed' : 'pointer',
                border: '1px solid rgba(255,255,255,0.1)',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>←</span> Previous
            </button>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              color: 'white',
              fontWeight: 'bold',
              boxShadow: '0 0 15px rgba(255,255,255,0.05)',
              fontSize: '14px'
            }}>
              {eventPage}
            </div>

            <button 
              disabled={events && events.length < 8}
              onClick={() => {
                setEventPage(p => p + 1);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="btn-glass"
              style={{ 
                padding: '10px 20px', 
                borderRadius: '10px', 
                background: (events && events.length < 8) ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)', 
                color: (events && events.length < 8) ? 'rgba(255,255,255,0.2)' : 'white', 
                cursor: (events && events.length < 8) ? 'not-allowed' : 'pointer',
                border: '1px solid rgba(255,255,255,0.1)',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              Next <span>→</span>
            </button>
          </div>
        </>
      )}
    </motion.div>
  );

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
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>
            {activeTab === 'automated' ? 'Automated ' : 'User '}
            <span className="gradient-text">{activeTab === 'automated' ? 'Tasks' : 'Events'}</span>
          </h1>
          <p style={{ color: 'var(--text-muted)' }}>
            {activeTab === 'automated'
              ? 'Review the automated background tasks performed by Cortex, based on the active (current) session.'
              : 'View and manage your scheduled reminders and events in the active (current) session.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '30px',
          background: 'rgba(255,255,255,0.03)',
          padding: '5px',
          borderRadius: '12px',
          width: 'fit-content'
        }}>
          <button
            onClick={() => setActiveTab('automated')}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: activeTab === 'automated' ? 'rgba(255,255,255,0.05)' : 'transparent',
              color: activeTab === 'automated' ? 'white' : 'var(--text-muted)',
              fontWeight: activeTab === 'automated' ? '600' : '400',
              transition: 'all 0.2s',
              cursor: 'pointer'
            }}
          >
            Automated Tasks
          </button>
          <button
            onClick={() => setActiveTab('reminders')}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: activeTab === 'reminders' ? 'rgba(255,255,255,0.05)' : 'transparent',
              color: activeTab === 'reminders' ? 'white' : 'var(--text-muted)',
              fontWeight: activeTab === 'reminders' ? '600' : '400',
              transition: 'all 0.2s',
              cursor: 'pointer'
            }}
          >
            User Events (Reminders)
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'automated' ? renderAutomatedTasks() : renderReminders()}
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
