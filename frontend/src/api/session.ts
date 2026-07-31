/**
 * 会话标识（sessionId）工具。
 *
 * 背景：考核标准要求前端生成并向后端传递统一的 sessionId，
 * 使一次面试从创建到出报告的所有请求可以被追踪、区分。
 *
 * 做法：打开应用时生成一个唯一 id，写入 sessionStorage，
 * 之后同一浏览器标签页内的所有请求都携带同一个 id（通过请求头传递，
 * 见 client.ts）。刷新页面仍保留，关闭标签页后失效。
 *
 * 注意：当前后端（server.ts）尚未读取这个请求头，这里只是把前端该做的部分
 * 补齐；后端接入时只需从 X-Session-Id 头里取值即可，无需改动前端。
 */

const STORAGE_KEY = 'interview-coach-session-id';

export function getSessionId(): string {
  let id = sessionStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
