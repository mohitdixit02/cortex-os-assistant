import React from 'react';
import { FaGlobe, FaDatabase, FaCalendarCheck, FaTools } from 'react-icons/fa';

export const TOOL_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string }> = {
    'web_search_01': { 
        label: "Web Search", 
        icon: FaGlobe, 
        color: "var(--accent-secondary)" 
    },
    'task_retriever_02': { 
        label: "Task Retrieval", 
        icon: FaDatabase, 
        color: "#10b981" 
    },
    'event_tool_03': { 
        label: "Event Tool", 
        icon: FaCalendarCheck, 
        color: "var(--accent-primary)" 
    }
};

interface ToolBadgeProps {
    tool_id?: string;
}

export const ToolBadge: React.FC<ToolBadgeProps> = ({ tool_id }) => {
    if (!tool_id) return null;

    const ids = tool_id.split(',').map(id => id.trim()).filter(Boolean);

    return (
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginTop: '8px' }}>
            {ids.map(id => {
                const config = TOOL_CONFIG[id] || { 
                    label: id, 
                    icon: FaTools, 
                    color: "var(--text-muted)" 
                };
                const Icon = config.icon;

                return (
                    <div
                        key={id}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                            background: 'rgba(167, 139, 250, 0.1)',
                            border: '1px solid rgba(167, 139, 250, 0.2)',
                            color: config.color,
                            fontSize: '10px',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontWeight: '600',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}
                    >
                        <Icon size={10} />
                        {config.label}
                    </div>
                );
            })}
        </div>
    );
};
