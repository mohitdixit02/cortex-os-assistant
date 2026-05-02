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
  created_at: string;
}

export interface Task {
  task_id: string;
  task_name: string;
  task_description?: string;
  status: string;
  created_at: string;
}

export function useThreads() {
  const { data, error, mutate } = useSWR<ChatThread[]>('/api/v1/chat/threads', (url) => apiClient(url));
  
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
    (url) => apiClient(url)
  );

  return {
    messages: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}

export function useTasks(page = 1, limit = 20) {
  const { data, error, mutate } = useSWR<Task[]>(
    [`/api/v1/tasks`, page, limit],
    ([url, p, l]) => apiClient(url as string, { params: { page: p as number, limit: l as number } })
  );

  return {
    tasks: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}
