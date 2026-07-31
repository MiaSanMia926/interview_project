<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-4">
    <div class="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-slate-200 p-8 space-y-6">
      <div class="text-center space-y-1">
        <h1 class="text-xl font-bold text-slate-800">面试突破助手</h1>
        <p class="text-sm text-slate-500">{{ isRegisterMode ? '创建账号' : '登录你的账号' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-600 mb-1">用户名</label>
          <input
            v-model="username"
            type="text"
            required
            minlength="3"
            maxlength="50"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="3-50个字符"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-600 mb-1">密码</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="6"
            maxlength="100"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="至少6位"
          />
        </div>

        <p v-if="errorMsg" class="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {{ errorMsg }}
        </p>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-bold py-2.5 rounded-lg transition-colors"
        >
          {{ isLoading ? '处理中...' : (isRegisterMode ? '注册并登录' : '登录') }}
        </button>
      </form>

      <div class="text-center text-xs text-slate-500">
        {{ isRegisterMode ? '已经有账号了？' : '还没有账号？' }}
        <button
          type="button"
          @click="isRegisterMode = !isRegisterMode; errorMsg = null"
          class="text-emerald-600 font-semibold hover:underline"
        >
          {{ isRegisterMode ? '去登录' : '去注册' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { api, setToken, ApiError } from '../api/client';

const emit = defineEmits<{
  (e: 'login-success', payload: { userId: string; username: string }): void;
}>();

const isRegisterMode = ref(false);
const username = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMsg = ref<string | null>(null);

const handleSubmit = async () => {
  errorMsg.value = null;
  isLoading.value = true;
  try {
    const result = isRegisterMode.value
      ? await api.register(username.value, password.value)
      : await api.login(username.value, password.value);

    setToken(result.token);
    emit('login-success', { userId: result.userId, username: result.username });
  } catch (e) {
    if (e instanceof ApiError) {
      // e.message 现在是 client.ts 从后端 {"detail": "..."} 里解析出来的真实原因
      // （用户名已被注册 / 用户名或密码错误 / 密码长度不够等），直接展示即可，
      // 不再用 e.kind 猜一个可能文不对题的固定文案。
      errorMsg.value = e.message || (isRegisterMode.value ? '注册失败，请重试' : '登录失败，请重试');
    } else {
      errorMsg.value = '发生未知错误，请重试';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>