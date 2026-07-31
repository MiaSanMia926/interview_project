/**
 * 统一 API 客户端 —— 基于 axios。
 *
 * 考核对应：Vibe Coding 合规性要求掌握 axios。
 * SSE 流式部分保留 fetch（axios 不支持 ReadableStream）。
 */
import axios, { AxiosError } from 'axios';
import type { Interview, InterviewSummary, UserProfile, Evaluation } from '../types';
import { getSessionId } from './session';

const TOKEN_KEY = 'interview-coach-token';

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const REQUEST_TIMEOUT_MS = 120000;

export type ApiErrorKind = 'network' | 'http' | 'business';

export class ApiError extends Error {
  kind: ApiErrorKind;
  status?: number;

  constructor(message: string, kind: ApiErrorKind, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
  }
}

// ── axios 实例 ──
const http = axios.create({
  baseURL: BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器：统一添加 sessionId + Authorization
http.interceptors.request.use((config) => {
  config.headers['X-Session-Id'] = getSessionId();
  const token = getToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一错误处理 → ApiError
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new ApiError('请求超时，请确认后端服务是否正常运行', 'network'));
    }
    if (!error.response) {
      return Promise.reject(new ApiError('无法连接后端服务，请检查服务是否已启动或网络是否正常', 'network'));
    }
    const status = error.response.status;
    const data: any = error.response.data;
    let detail: string | undefined;
    if (data && typeof data.detail === 'string') {
      detail = data.detail;
    } else if (data && Array.isArray(data.detail)) {
      detail = data.detail.map((item: any) => item?.msg).filter(Boolean).join('；');
    }
    return Promise.reject(new ApiError(detail ?? `接口请求失败（HTTP ${status}）`, 'http', status));
  }
);

// ── 类型 ──
interface HealthResponse { status: string; hasGeminiKey: boolean; hasDeepseekKey?: boolean }
interface AuthResponse { token: string; userId: string; username: string }
interface InterviewListResponse { total: number; page: number; size: number; items: Interview[] }
interface CreateInterviewPayload { userId: string; targetCompany: string; targetPosition: string; techStack: string[]; interviewMode: string }
interface AnswerResponse { interviewId: string; currentPhase: string; questionIndex: number; nextAction: string; nextMessage: string; evaluation: Evaluation | null; isFinished: boolean }
interface SuggestPositionsResponse { positions: string[] }

// ── API 方法 ──
export const api = {
  getHealth: () => http.get<HealthResponse>('/api/health').then(r => r.data),

  register: (username: string, password: string) =>
    http.post<AuthResponse>('/api/auth/register', { username, password }).then(r => r.data),

  login: (username: string, password: string) =>
    http.post<AuthResponse>('/api/auth/login', { username, password }).then(r => r.data),

  logout: () => http.post('/api/auth/logout'),

  getMe: () => http.get<{ id: string; username: string; createdAt: string }>('/api/users/me').then(r => r.data),

  getHistory: async () => {
    const data = await http.get<InterviewListResponse>('/api/interviews').then(r => r.data);
    if (data && Array.isArray((data as any).items)) return (data as InterviewListResponse).items;
    return data as unknown as Interview[];
  },

  createInterview: (payload: CreateInterviewPayload) =>
    http.post<Interview>('/api/interviews', payload).then(r => r.data),

  startInterview: (interviewId: string) =>
    http.post<Interview>(`/api/interviews/${interviewId}/start`).then(r => r.data),

  submitAnswer: (interviewId: string, questionId: string, userAnswer: string) =>
    http.post<AnswerResponse>(`/api/interviews/${interviewId}/answer`, { questionId, userAnswer }).then(r => r.data),

  skipQuestion: (interviewId: string) =>
    http.post<AnswerResponse>(`/api/interviews/${interviewId}/skip`).then(r => r.data),

  getSummary: (interviewId: string) =>
    http.get<InterviewSummary>(`/api/interviews/${interviewId}/summary`).then(r => r.data),

  getProfile: (userId: string) => http.get<UserProfile>(`/api/users/${userId}/profile`).then(r => r.data),

  suggestPositions: (targetCompany: string) =>
    http.post<SuggestPositionsResponse>('/api/positions/suggest', { targetCompany }).then(r => r.data),
};

// ── SSE 流式（保留 fetch，axios 不支持流式） ──

export async function streamPreviewQuestion(
  interviewId: string,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (msg: string) => void
) {
  const headers: Record<string, string> = { 'X-Session-Id': getSessionId() };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}/api/interviews/${interviewId}/preview-question/stream`, { method: 'POST', headers });
  await readSSEStream(response, onChunk, onDone, onError);
}

export async function streamPreviewFeedback(
  interviewId: string, questionId: string, userAnswer: string,
  onScore: (evaluation: any) => void,
  onChunk: (text: string) => void, onDone: () => void, onError: (msg: string) => void
) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', 'X-Session-Id': getSessionId() };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}/api/interviews/${interviewId}/preview-feedback/stream`, {
    method: 'POST', headers, body: JSON.stringify({ questionId, userAnswer })
  });
  await readSSEStream(response, onChunk, onDone, onError, onScore);
}

async function readSSEStream(response: Response, onChunk: (text: string) => void, onDone: () => void, onError: (msg: string) => void, onScore?: (evaluation: any) => void) {
  if (!response.body) { onError('浏览器不支持流式读取'); return; }
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';
    for (const part of parts) {
      if (!part.startsWith('data: ')) continue;
      try {
        const msg = JSON.parse(part.slice(6));
        if (msg.type === 'chunk') onChunk(msg.content);
        else if (msg.type === 'score' && onScore) onScore(msg.evaluation);
        else if (msg.type === 'done') onDone();
        else if (msg.type === 'error') onError(msg.message);
      } catch { /* ignore */ }
    }
  }
}
