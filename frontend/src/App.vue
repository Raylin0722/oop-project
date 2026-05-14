<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';

const API_ORIGIN = `${window.location.protocol}//${window.location.hostname}:8000`;
const API_BASE = `${API_ORIGIN}/api`;
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000/ws`;

const activeTab = ref('register');
const loading = ref(false);
const message = ref('');
const error = ref('');
const currentUser = ref(null);
const currentRoom = ref(null);
const matchmakingTicket = ref(null);
const showJoinRoom = ref(false);
const showRegisterPassword = ref(false);
const showLoginPassword = ref(false);
const showResetPassword = ref(false);
let roomSocket = null;
let matchmakingSocket = null;
let matchmakingClock = null;

const registerForm = reactive({
  username: '',
  nickname: '',
  email: '',
  password: '',
  password_confirm: '',
});

const verifyForm = reactive({
  email: '',
  code: '',
});

const loginForm = reactive({
  username: '',
  password: '',
});

const resetForm = reactive({
  email: '',
  token: '',
  new_password: '',
  new_password_confirm: '',
});

const joinRoomForm = reactive({
  code: '',
});

const isLoggedIn = computed(() => Boolean(currentUser.value));
const isInRoom = computed(() => Boolean(currentRoom.value));
const isPlayingRoom = computed(() => currentRoom.value?.status === 'Playing');
const isMatchmaking = computed(() => Boolean(matchmakingTicket.value));
const matchmakingWaitedFor = computed(() => matchmakingTicket.value?.waited_for ?? 0);
const matchmakingTimeout = computed(() => matchmakingTicket.value?.timeout_seconds ?? 30);
const matchmakingScoreWindow = computed(() => matchmakingTicket.value?.score_window ?? 100);
const roomMembers = computed(() => currentRoom.value?.members || []);
const roomSlots = computed(() => {
  const slots = [...roomMembers.value];
  while (slots.length < 4) {
    slots.push(null);
  }
  return slots;
});
const currentRoomMember = computed(() => (
  roomMembers.value.find((member) => member.user?.id === currentUser.value?.id) || null
));
const isCurrentUserHost = computed(() => currentRoom.value?.host_id === currentUser.value?.id);
const isCurrentUserReady = computed(() => Boolean(currentRoomMember.value?.is_ready));
const hasResetToken = computed(() => Boolean(resetForm.token));
const lobbyDisplayName = computed(() => currentUser.value?.nickname || currentUser.value?.username || 'Player');
const trophyCount = computed(() => currentUser.value?.total_score ?? 0);
const passwordIconTitle = computed(() => (showRegisterPassword.value ? 'Hide password' : 'Show password'));
const loginPasswordIconTitle = computed(() => (showLoginPassword.value ? 'Hide password' : 'Show password'));
const resetPasswordIconTitle = computed(() => (showResetPassword.value ? 'Hide password' : 'Show password'));

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error?.message || 'Request failed.');
  }

  return data;
}

function setFeedback(successMessage = '') {
  message.value = successMessage;
  error.value = '';
}

function setError(err) {
  error.value = err.message || 'Something went wrong.';
  message.value = '';
}

function clearFeedback() {
  message.value = '';
  error.value = '';
}

function clearRegisterForm() {
  registerForm.username = '';
  registerForm.nickname = '';
  registerForm.email = '';
  registerForm.password = '';
  registerForm.password_confirm = '';
}

function clearVerifyForm() {
  verifyForm.email = '';
  verifyForm.code = '';
}

function clearLoginForm() {
  loginForm.username = '';
  loginForm.password = '';
}

function clearResetForm(keepEmail = false) {
  const email = resetForm.email;
  resetForm.email = keepEmail ? email : '';
  resetForm.token = '';
  resetForm.new_password = '';
  resetForm.new_password_confirm = '';
}

function clearJoinRoomForm() {
  joinRoomForm.code = '';
}

function clearForms() {
  clearRegisterForm();
  clearVerifyForm();
  clearLoginForm();
  clearResetForm();
  clearJoinRoomForm();
}

function switchTab(tab) {
  if (isLoggedIn.value && tab !== 'success') {
    activeTab.value = 'success';
    setFeedback('You are already logged in. Please logout before switching accounts.');
    return;
  }
  clearFeedback();
  clearForms();
  activeTab.value = tab;
}

async function submitRegister() {
  if (registerForm.password !== registerForm.password_confirm) {
    setError(new Error('Passwords do not match.'));
    return;
  }
  loading.value = true;
  try {
    const data = await request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(registerForm),
    });
    currentUser.value = data.user;
    verifyForm.email = registerForm.email;
    clearRegisterForm();
    activeTab.value = 'verify';
    setFeedback('Registration successful. Please enter the email verification code.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function submitVerify() {
  loading.value = true;
  try {
    const data = await request('/auth/verify-email/', {
      method: 'POST',
      body: JSON.stringify(verifyForm),
    });
    currentUser.value = data.user;
    clearVerifyForm();
    activeTab.value = 'login';
    setFeedback('Email verified. You can log in now.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function submitLogin() {
  loading.value = true;
  try {
    const data = await request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(loginForm),
    });
    currentUser.value = data.user;
    clearLoginForm();
    activeTab.value = 'success';
    connectMatchmakingSocket();
    await loadCurrentRoom(false);
    await loadMatchmakingStatus(false);
    clearFeedback();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function submitRequestPasswordReset() {
  loading.value = true;
  try {
    await request('/auth/request-password-reset/', {
      method: 'POST',
      body: JSON.stringify({ email: resetForm.email }),
    });
    clearResetForm(true);
    setFeedback('If the email is registered, a password reset link has been sent.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function submitResetPassword() {
  if (resetForm.new_password !== resetForm.new_password_confirm) {
    setError(new Error('Passwords do not match.'));
    return;
  }
  loading.value = true;
  try {
    await request('/auth/reset-password/', {
      method: 'POST',
      body: JSON.stringify(resetForm),
    });
    clearResetForm();
    activeTab.value = 'login';
    setFeedback('Password reset successful. You can log in now.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function submitLogout() {
  loading.value = true;
  try {
    await request('/auth/logout/', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    currentUser.value = null;
    currentRoom.value = null;
    matchmakingTicket.value = null;
    disconnectRoomSocket();
    disconnectMatchmakingSocket();
    stopMatchmakingClock();
    activeTab.value = 'login';
    setFeedback('Logged out.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

function normalizeRoomCode() {
  joinRoomForm.code = joinRoomForm.code.replace(/\D/g, '').slice(0, 6);
}

async function loadCurrentRoom(showErrors = true) {
  if (!isLoggedIn.value) {
    currentRoom.value = null;
    return;
  }
  try {
    const data = await request('/rooms/current/');
    currentRoom.value = data.room;
    if (currentRoom.value) {
      connectRoomSocket(currentRoom.value.code);
    } else {
      disconnectRoomSocket();
    }
  } catch (err) {
    currentRoom.value = null;
    disconnectRoomSocket();
    if (showErrors) {
      setError(err);
    }
  }
}

async function loadMatchmakingStatus(showErrors = true) {
  if (!isLoggedIn.value) {
    matchmakingTicket.value = null;
    return;
  }
  try {
    const data = await request('/matchmaking/status/');
    matchmakingTicket.value = data.ticket;
    if (matchmakingTicket.value) {
      startMatchmakingClock();
    } else {
      stopMatchmakingClock();
    }
    if (data.room) {
      currentRoom.value = data.room;
      matchmakingTicket.value = null;
      stopMatchmakingClock();
      connectRoomSocket(currentRoom.value.code);
    }
  } catch (err) {
    matchmakingTicket.value = null;
    if (showErrors) {
      setError(err);
    }
  }
}

function connectRoomSocket(code) {
  if (!code) {
    disconnectRoomSocket();
    return;
  }
  if (roomSocket && roomSocket.readyState !== WebSocket.CLOSED && roomSocket.roomCode === code) {
    return;
  }

  disconnectRoomSocket();
  roomSocket = new WebSocket(`${WS_BASE}/rooms/${code}/`);
  roomSocket.roomCode = code;

  roomSocket.addEventListener('message', (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === 'room_update') {
      currentRoom.value = payload.room;
      return;
    }
    if (payload.type === 'room_deleted' || payload.type === 'room_left') {
      currentRoom.value = null;
      disconnectRoomSocket();
    }
  });

  roomSocket.addEventListener('close', () => {
    if (roomSocket?.roomCode === code) {
      roomSocket = null;
    }
  });
}

function disconnectRoomSocket() {
  if (roomSocket) {
    const socket = roomSocket;
    roomSocket = null;
    socket.close();
  }
}

function connectMatchmakingSocket() {
  if (!isLoggedIn.value) {
    disconnectMatchmakingSocket();
    return;
  }
  if (matchmakingSocket && matchmakingSocket.readyState !== WebSocket.CLOSED) {
    return;
  }

  matchmakingSocket = new WebSocket(`${WS_BASE}/matchmaking/`);

  matchmakingSocket.addEventListener('message', (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === 'waiting') {
      matchmakingTicket.value = payload.ticket;
      startMatchmakingClock();
      return;
    }
    if (payload.type === 'matched') {
      matchmakingTicket.value = null;
      stopMatchmakingClock();
      currentRoom.value = payload.room;
      connectRoomSocket(currentRoom.value.code);
      return;
    }
    if (payload.type === 'idle' || payload.type === 'cancelled') {
      matchmakingTicket.value = null;
      stopMatchmakingClock();
    }
  });

  matchmakingSocket.addEventListener('close', () => {
    matchmakingSocket = null;
  });
}

function startMatchmakingClock() {
  stopMatchmakingClock();
  matchmakingClock = window.setInterval(() => {
    if (!matchmakingTicket.value) {
      stopMatchmakingClock();
      return;
    }
    matchmakingTicket.value = {
      ...matchmakingTicket.value,
      waited_for: Math.min(
        matchmakingTicket.value.waited_for + 1,
        matchmakingTicket.value.timeout_seconds,
      ),
      score_window: matchmakingWindowForWait(
        Math.min(
          matchmakingTicket.value.waited_for + 1,
          matchmakingTicket.value.timeout_seconds,
        ),
      ),
    };
  }, 1000);
}

function matchmakingWindowForWait(waitedFor) {
  if (waitedFor >= 20) {
    return 300;
  }
  if (waitedFor >= 10) {
    return 200;
  }
  return 100;
}

function stopMatchmakingClock() {
  if (matchmakingClock) {
    window.clearInterval(matchmakingClock);
    matchmakingClock = null;
  }
}

function disconnectMatchmakingSocket() {
  if (matchmakingSocket) {
    const socket = matchmakingSocket;
    matchmakingSocket = null;
    socket.close();
  }
}

async function createRoom() {
  loading.value = true;
  try {
    const data = await request('/rooms/create/', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    currentRoom.value = data.room;
    matchmakingTicket.value = null;
    stopMatchmakingClock();
    showJoinRoom.value = false;
    clearFeedback();
    connectRoomSocket(currentRoom.value.code);
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

function openJoinRoom() {
  clearFeedback();
  clearJoinRoomForm();
  showJoinRoom.value = true;
}

function closeJoinRoom() {
  showJoinRoom.value = false;
  clearJoinRoomForm();
}

async function joinRoom() {
  normalizeRoomCode();
  if (joinRoomForm.code.length !== 6) {
    setError(new Error('請輸入六碼房間代碼。'));
    return;
  }

  loading.value = true;
  try {
    const data = await request('/rooms/join/', {
      method: 'POST',
      body: JSON.stringify({ code: joinRoomForm.code }),
    });
    currentRoom.value = data.room;
    matchmakingTicket.value = null;
    stopMatchmakingClock();
    closeJoinRoom();
    clearFeedback();
    connectRoomSocket(currentRoom.value.code);
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function startMatchmaking() {
  loading.value = true;
  try {
    const data = await request('/matchmaking/join/', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    matchmakingTicket.value = data.ticket;
    if (matchmakingTicket.value) {
      startMatchmakingClock();
    }
    if (data.room) {
      currentRoom.value = data.room;
      matchmakingTicket.value = null;
      stopMatchmakingClock();
      connectRoomSocket(currentRoom.value.code);
    }
    connectMatchmakingSocket();
    clearFeedback();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function cancelMatchmaking() {
  loading.value = true;
  try {
    await request('/matchmaking/cancel/', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    matchmakingTicket.value = null;
    stopMatchmakingClock();
    clearFeedback();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function toggleReady() {
  if (!currentRoom.value) {
    return;
  }

  loading.value = true;
  try {
    const data = await request(`/rooms/${currentRoom.value.code}/ready/`, {
      method: 'POST',
      body: JSON.stringify({ is_ready: !isCurrentUserReady.value }),
    });
    currentRoom.value = data.room;
    clearFeedback();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function leaveRoom() {
  if (!currentRoom.value) {
    return;
  }

  loading.value = true;
  try {
    await request(`/rooms/${currentRoom.value.code}/leave/`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
    currentRoom.value = null;
    clearFeedback();
    disconnectRoomSocket();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function kickMember(member) {
  if (!currentRoom.value || !member) {
    return;
  }

  loading.value = true;
  try {
    const data = await request(`/rooms/${currentRoom.value.code}/kick/`, {
      method: 'POST',
      body: JSON.stringify({ user_id: member.user.id }),
    });
    currentRoom.value = data.room;
    clearFeedback();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function transferHost(member) {
  if (!currentRoom.value || !member) {
    return;
  }

  loading.value = true;
  try {
    const data = await request(`/rooms/${currentRoom.value.code}/transfer-host/`, {
      method: 'POST',
      body: JSON.stringify({ user_id: member.user.id }),
    });
    currentRoom.value = data.room;
    clearFeedback();
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function startGame() {
  if (!currentRoom.value) {
    return;
  }

  loading.value = true;
  try {
    const data = await request(`/rooms/${currentRoom.value.code}/start/`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
    currentRoom.value = data.room;
    setFeedback(data.message || 'Game started.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function endGame() {
  if (!currentRoom.value) {
    return;
  }

  loading.value = true;
  try {
    await request(`/rooms/${currentRoom.value.code}/end/`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
    currentRoom.value = null;
    disconnectRoomSocket();
    setFeedback('Game ended.');
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  const params = new URLSearchParams(window.location.search);
  const resetEmail = params.get('reset_email');
  const resetToken = params.get('reset_token');
  if (resetEmail && resetToken) {
    resetForm.email = resetEmail;
    resetForm.token = resetToken;
    activeTab.value = 'forgot';
    window.history.replaceState({}, '', window.location.pathname);
    setFeedback('Reset link loaded. Enter a new password.');
    return;
  }

  try {
    const data = await request('/auth/me/');
    currentUser.value = data.user;
    activeTab.value = 'success';
    connectMatchmakingSocket();
    await loadCurrentRoom(false);
    await loadMatchmakingStatus(false);
  } catch {
    currentUser.value = null;
  }
});

onUnmounted(() => {
  disconnectRoomSocket();
  disconnectMatchmakingSocket();
  stopMatchmakingClock();
});
</script>

<template>
  <main class="auth-page" :class="{ 'lobby-page': activeTab === 'success' && isLoggedIn }">
    <section class="auth-shell" :class="{ 'lobby-shell': activeTab === 'success' && isLoggedIn }">
      <header class="page-header">
        <h1>OOP Game Account</h1>
      </header>

      <nav v-if="!(activeTab === 'success' && isLoggedIn)" class="tabs" aria-label="Account pages">
        <button
          :class="{ active: activeTab === 'register' }"
          :disabled="isLoggedIn"
          type="button"
          @click="switchTab('register')"
        >
          Register
        </button>
        <button
          :class="{ active: activeTab === 'verify' }"
          :disabled="isLoggedIn"
          type="button"
          @click="switchTab('verify')"
        >
          Verify
        </button>
        <button
          :class="{ active: activeTab === 'login' }"
          :disabled="isLoggedIn"
          type="button"
          @click="switchTab('login')"
        >
          Login
        </button>
        <button
          :class="{ active: activeTab === 'forgot' }"
          :disabled="isLoggedIn"
          type="button"
          @click="switchTab('forgot')"
        >
          Forgot
        </button>
      </nav>

      <p v-if="message" class="notice success">{{ message }}</p>
      <p v-if="error" class="notice error">{{ error }}</p>

      <form v-if="activeTab === 'register'" class="auth-form" @submit.prevent="submitRegister">
        <label>
          Username
          <input v-model.trim="registerForm.username" autocomplete="username" required type="text" />
        </label>
        <label>
          Nickname
          <input v-model.trim="registerForm.nickname" autocomplete="nickname" type="text" />
        </label>
        <label>
          Email
          <input v-model.trim="registerForm.email" autocomplete="email" required type="email" />
        </label>
        <label>
          Password
          <span class="password-control">
            <input
              v-model="registerForm.password"
              autocomplete="new-password"
              minlength="8"
              required
              :type="showRegisterPassword ? 'text' : 'password'"
            />
            <button
              class="icon-button"
              type="button"
              :aria-label="passwordIconTitle"
              :title="passwordIconTitle"
              @click="showRegisterPassword = !showRegisterPassword"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </span>
        </label>
        <label>
          Confirm Password
          <span class="password-control">
            <input
              v-model="registerForm.password_confirm"
              autocomplete="new-password"
              minlength="8"
              required
              :type="showRegisterPassword ? 'text' : 'password'"
            />
            <button
              class="icon-button"
              type="button"
              :aria-label="passwordIconTitle"
              :title="passwordIconTitle"
              @click="showRegisterPassword = !showRegisterPassword"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </span>
        </label>
        <button class="primary-action" :disabled="loading" type="submit">
          {{ loading ? 'Submitting...' : 'Create Account' }}
        </button>
      </form>

      <form v-if="activeTab === 'verify'" class="auth-form" @submit.prevent="submitVerify">
        <label>
          Email
          <input v-model.trim="verifyForm.email" autocomplete="email" required type="email" />
        </label>
        <label>
          Verification Code
          <input v-model.trim="verifyForm.code" inputmode="numeric" maxlength="6" required type="text" />
        </label>
        <button class="primary-action" :disabled="loading" type="submit">
          {{ loading ? 'Verifying...' : 'Verify Email' }}
        </button>
      </form>

      <form v-if="activeTab === 'login'" class="auth-form" @submit.prevent="submitLogin">
        <label>
          Username or Email
          <input v-model.trim="loginForm.username" autocomplete="username" required type="text" />
        </label>
        <label>
          Password
          <span class="password-control">
            <input
              v-model="loginForm.password"
              autocomplete="current-password"
              required
              :type="showLoginPassword ? 'text' : 'password'"
            />
            <button
              class="icon-button"
              type="button"
              :aria-label="loginPasswordIconTitle"
              :title="loginPasswordIconTitle"
              @click="showLoginPassword = !showLoginPassword"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </span>
        </label>
        <button class="primary-action" :disabled="loading" type="submit">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <form v-if="activeTab === 'forgot' && !hasResetToken" class="auth-form" @submit.prevent="submitRequestPasswordReset">
        <label>
          Email
          <input v-model.trim="resetForm.email" autocomplete="email" required type="email" />
        </label>
        <button
          class="secondary-action"
          :disabled="loading || !resetForm.email"
          type="submit"
        >
          {{ loading ? 'Sending...' : 'Send Reset Link' }}
        </button>
      </form>

      <form v-if="activeTab === 'forgot' && hasResetToken" class="auth-form" @submit.prevent="submitResetPassword">
        <label>
          Email
          <input v-model.trim="resetForm.email" autocomplete="email" required readonly type="email" />
        </label>
        <input v-model="resetForm.token" type="hidden" />
        <label>
          New Password
          <span class="password-control">
            <input
              v-model="resetForm.new_password"
              autocomplete="new-password"
              minlength="8"
              required
              :type="showResetPassword ? 'text' : 'password'"
            />
            <button
              class="icon-button"
              type="button"
              :aria-label="resetPasswordIconTitle"
              :title="resetPasswordIconTitle"
              @click="showResetPassword = !showResetPassword"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </span>
        </label>
        <label>
          Confirm New Password
          <span class="password-control">
            <input
              v-model="resetForm.new_password_confirm"
              autocomplete="new-password"
              minlength="8"
              required
              :type="showResetPassword ? 'text' : 'password'"
            />
            <button
              class="icon-button"
              type="button"
              :aria-label="resetPasswordIconTitle"
              :title="resetPasswordIconTitle"
              @click="showResetPassword = !showResetPassword"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </span>
        </label>
        <button class="primary-action" :disabled="loading" type="submit">
          {{ loading ? 'Resetting...' : 'Reset Password' }}
        </button>
      </form>

      <section v-if="activeTab === 'success' && isLoggedIn && isPlayingRoom" class="test-game-page" aria-label="Test game">
        <header class="test-game-topbar">
          <div>
            <span class="room-code">房間代碼 {{ currentRoom.code }}</span>
            <h1>測試遊戲頁</h1>
          </div>
          <button class="lobby-logout" :disabled="loading" type="button" @click="submitLogout">
            Logout
          </button>
        </header>

        <div class="test-game-board">
          <div
            v-for="(member, index) in roomSlots"
            :key="member ? (member.is_ai ? `game-ai-${index}` : member.user.id) : `game-empty-${index}`"
            class="test-player"
            :class="{ ai: member?.is_ai }"
          >
            <div class="seat-avatar" aria-hidden="true">
              {{ member ? (member.user.nickname || member.user.username).charAt(0).toUpperCase() : '+' }}
            </div>
            <strong>{{ member ? (member.user.nickname || member.user.username) : '空位' }}</strong>
            <span>{{ member?.is_ai ? 'AI 玩家' : '真人玩家' }}</span>
          </div>
        </div>

        <button class="end-game-action" :disabled="loading" type="button" @click="endGame">
          {{ loading ? '結束中...' : '結束遊戲' }}
        </button>
      </section>

      <section v-if="activeTab === 'success' && isLoggedIn && !isPlayingRoom" class="game-lobby" aria-label="Game lobby">
        <header class="lobby-topbar">
          <div class="player-summary" aria-label="Player summary">
            <div class="player-avatar" aria-hidden="true">
              {{ lobbyDisplayName.charAt(0).toUpperCase() }}
            </div>
            <div class="player-info">
              <span class="player-name">{{ lobbyDisplayName }}</span>
              <span class="player-trophies">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="M8 4h8v3a4 4 0 0 1-8 0V4Z" />
                  <path d="M8 6H4v1a4 4 0 0 0 4 4" />
                  <path d="M16 6h4v1a4 4 0 0 1-4 4" />
                  <path d="M12 11v5" />
                  <path d="M9 20h6" />
                  <path d="M10 16h4l1 4H9l1-4Z" />
                </svg>
                {{ trophyCount }} 獎盃數
              </span>
              <span v-if="isInRoom" class="room-code">房間代碼 {{ currentRoom.code }}</span>
            </div>
          </div>

          <button class="lobby-logout" :disabled="loading" type="button" @click="submitLogout">
            Logout
          </button>
        </header>

        <div class="lobby-stage" :class="{ 'room-stage': isInRoom }">
          <template v-if="isInRoom">
            <article
              v-for="(member, index) in roomSlots"
              :key="member ? (member.is_ai ? `ai-${index}` : member.user.id) : `empty-${index}`"
              class="room-seat"
              :class="{ empty: !member, ready: member?.is_ready, ai: member?.is_ai }"
            >
              <div class="seat-avatar" aria-hidden="true">
                {{ member ? (member.user.nickname || member.user.username).charAt(0).toUpperCase() : '+' }}
              </div>
              <div class="seat-details">
                <strong>{{ member ? (member.user.nickname || member.user.username) : '等待玩家' }}</strong>
                <span v-if="member?.is_ai">AI 玩家</span>
                <span v-else-if="member?.is_host">房主</span>
                <span v-else-if="member?.is_ready">已準備</span>
                <span v-else-if="member">未準備</span>
                <span v-else>空位</span>
              </div>
              <div
                v-if="member && !member.is_ai && isCurrentUserHost && member.user.id !== currentUser.id"
                class="seat-controls"
              >
                <button type="button" @click="transferHost(member)">
                  轉讓
                </button>
                <button type="button" @click="kickMember(member)">
                  剔除
                </button>
              </div>
            </article>
          </template>
          <div v-else class="stage-title">Game Lobby</div>
        </div>

        <div class="lobby-actions" aria-label="Lobby actions">
          <template v-if="isInRoom">
            <button
              v-if="!isPlayingRoom"
              class="lobby-action join-room"
              :disabled="loading"
              type="button"
              @click="toggleReady"
            >
              {{ isCurrentUserReady ? '取消準備' : '準備完成' }}
            </button>
            <button v-else class="lobby-action join-room" disabled type="button">
              遊戲已開始
            </button>
            <button class="lobby-action create-room" :disabled="loading" type="button" @click="leaveRoom">
              離開房間
            </button>
            <button
              v-if="!isPlayingRoom"
              class="lobby-action start-match"
              :disabled="loading || !isCurrentUserHost || !currentRoom.can_start"
              type="button"
              @click="startGame"
            >
              開始遊戲
            </button>
            <button v-else class="lobby-action start-match" disabled type="button">
              等待遊戲畫面
            </button>
          </template>
          <template v-else>
            <button class="lobby-action create-room" :disabled="loading || isMatchmaking" type="button" @click="createRoom">
            創建房間
            </button>
            <button class="lobby-action join-room" :disabled="loading || isMatchmaking" type="button" @click="openJoinRoom">
              加入房間
            </button>
            <button
              v-if="!isMatchmaking"
              class="lobby-action start-match"
              :disabled="loading"
              type="button"
              @click="startMatchmaking"
            >
              開始配對
            </button>
            <button
              v-else
              class="lobby-action start-match"
              :disabled="loading"
              type="button"
              @click="cancelMatchmaking"
            >
              配對中 {{ matchmakingWaitedFor }}/{{ matchmakingTimeout }} 秒 ±{{ matchmakingScoreWindow }} 盃
            </button>
          </template>
        </div>

        <div v-if="showJoinRoom" class="join-room-backdrop" role="presentation" @click.self="closeJoinRoom">
          <form class="join-room-dialog" @submit.prevent="joinRoom">
            <h2>加入房間</h2>
            <label>
              六碼房間代碼
              <input
                v-model="joinRoomForm.code"
                autocomplete="off"
                inputmode="numeric"
                maxlength="6"
                pattern="[0-9]{6}"
                required
                type="text"
                @input="normalizeRoomCode"
              />
            </label>
            <div class="dialog-actions">
              <button class="secondary-action" type="button" @click="closeJoinRoom">
                取消
              </button>
              <button class="primary-action" :disabled="loading || joinRoomForm.code.length !== 6" type="submit">
                確認加入
              </button>
            </div>
          </form>
        </div>
      </section>
    </section>
  </main>
</template>
