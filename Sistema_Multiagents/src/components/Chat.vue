<template>
    <div>
      <h2 class="text-xl font-bold mb-2">Xat amb el teu agent</h2>
      <div class="mb-4">
        <input v-model="input" @keyup.enter="enviar" placeholder="Escriu aquí..." class="border p-2 w-full" />
      </div>
      <div class="bg-gray-100 p-4 rounded h-64 overflow-y-scroll">
        <div v-for="(msg, i) in historial" :key="i" class="mb-2">
          <strong>{{ msg.rol }}:</strong> {{ msg.text }}
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  
  const input = ref('')
  const historial = ref([])
  
  const enviar = async () => {
    if (!input.value.trim()) return
  
    historial.value.push({ rol: 'Tu', text: input.value })
    try {
      const resposta = await axios.post('http://localhost:5000/chat', {
        message: input.value,
      })
      historial.value.push({ rol: 'Agent', text: resposta.data.response })
    } catch (err) {
      historial.value.push({ rol: 'Agent', text: '❌ Error connectant amb el servidor.' })
    }
    input.value = ''
  }
  </script>
  