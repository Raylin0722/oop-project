<script setup>
import { ref } from 'vue';

const isLoading = ref(false);

function handleJoinRoom() {
  console.log('Join room clicked');
  // TODO: Implement join room functionality
}

function handleStartGame() {
  console.log('Start game clicked');
  // TODO: Implement start game functionality
}
</script>

<template>
  <div class="action-buttons">
    <button class="action-btn join-btn" :disabled="isLoading" @click="handleJoinRoom">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" fill="currentColor"/>
      </svg>
      加入房間
    </button>
    <button class="action-btn start-btn" :disabled="isLoading" @click="handleStartGame">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 5v14l11-7z" fill="currentColor"/>
      </svg>
      開始遊戲
    </button>
  </div>
</template>

<style scoped>
.action-buttons {
  position: absolute;
  bottom: 32px;
  right: 32px;
  display: flex;
  gap: 12px;
  flex-direction: column;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
  min-width: 140px;
}

.action-btn svg {
  width: 20px;
  height: 20px;
  stroke-width: 0;
}

.join-btn {
  background: #1d4ed8;
  color: #ffffff;
  border: 1px solid #1e40af;
}

.join-btn:hover:not(:disabled) {
  background: #1e40af;
  box-shadow: 0 8px 20px rgba(29, 78, 216, 0.3);
  transform: translateY(-2px);
}

.start-btn {
  background: #10b981;
  color: #ffffff;
  border: 1px solid #059669;
}

.start-btn:hover:not(:disabled) {
  background: #059669;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
  transform: translateY(-2px);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1);
}

@media (max-width: 768px) {
  .action-buttons {
    bottom: 16px;
    right: 16px;
    flex-direction: row;
  }

  .action-btn {
    min-width: 120px;
    padding: 10px 16px;
    font-size: 13px;
  }

  .action-btn svg {
    width: 18px;
    height: 18px;
  }
}
</style>
