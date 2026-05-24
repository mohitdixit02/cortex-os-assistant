import useSWR from 'swr';
import { apiClient } from '../utility/apiClient';

// Types from backend response models
export interface ChatThread {
  session_id: string;
  user_id: string;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  message_id: string;
  session_id: string;
  user_id: string;
  content: string;
  role: string;
  is_refined_query?: boolean;
  refined_query?: string;
  tool_id?: string;
  created_at: string;
}

export interface Task {
  task_id: string;
  task_name: string;
  task_description?: string;
  status: string;
  tool_id?: string;
  created_at: string;
}

export interface UserEvent {
  id: string;
  name: string;
  event_description?: string;
  trigger_time: string;
  status: string;
  created_at: string;
}

export function useThreads() {
  const { data, error, mutate } = useSWR<ChatThread[]>('/api/v1/chat/threads', (url: string) => apiClient<ChatThread[]>(url));
  
  return {
    threads: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}

export function useMessages(threadId: string | null) {
  const { data, error, mutate } = useSWR<Message[]>(
    threadId ? `/api/v1/chat/threads/${threadId}/messages` : null,
    (url: string) => apiClient<Message[]>(url)
  );

  return {
    messages: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}

export function useTasks(page = 1, limit = 8, sessionId?: string | null) {
  const { data, error, mutate } = useSWR<Task[]>(
    [`/api/v1/tasks`, page, limit, sessionId],
    ([url, p, l, s]) => {
      const params: any = { page: p as number, limit: l as number };
      if (s) params.session_id = s;
      return apiClient(url as string, { params });
    }
  );

  return {
    tasks: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}

export function useEvents(page = 1, limit = 8, sessionId?: string | null) {
  const { data, error, mutate } = useSWR<UserEvent[]>(
    [`/api/v1/events`, page, limit, sessionId],
    ([url, p, l, s]) => {
      const params: any = { page: p as number, limit: l as number };
      if (s) params.session_id = s;
      return apiClient(url as string, { params });
    }
  );

  return {
    events: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}
