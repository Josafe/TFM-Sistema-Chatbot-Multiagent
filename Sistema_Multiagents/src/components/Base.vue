<!-- components/Chat.vue -->
<template>
    <div class="chat-box">
      <div class="messages">
        <div v-for="(msg, i) in messages" :key="i">
          <strong>{{ msg.sender }}:</strong> {{ msg.text }}
        </div>
      </div>
      <form @submit.prevent="sendMessage">
        <input v-model="newMessage" placeholder="agent1: fes això" />
        <button type="submit">Envia</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  
  const messages = ref([]);
  const newMessage = ref('');
  let socket = null;
  
  onMounted(() => {
    socket = new WebSocket('ws://localhost:8000/ws');
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      messages.value.push(data);
    };
  });
  
  function sendMessage() {
    if (socket && newMessage.value.trim()) {
      socket.send(newMessage.value.trim());
      newMessage.value = '';
    }
  }
  </script>
  
  <style scoped>
  .chat-box {
    max-width: 600px;
    margin: auto;
    padding: 1rem;
  }
  .messages {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #ccc;
    margin-bottom: 1rem;
    padding: 0.5rem;
  }
  </style>
  