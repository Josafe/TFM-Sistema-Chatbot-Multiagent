<template>
  <div class="container">
    <h1>🤖 Chat amb l'Agent Git</h1>
    <textarea v-model="message" placeholder="Escriu una instrucció com 'clona el repo' o 'instal·la dependències'"></textarea>
    <button @click="sendMessage">Enviar</button>
    <div v-if="response" class="response">
      <strong>Resposta:</strong>
      <p>{{ response }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      message: '',
      response: ''
    }
  },
  methods: {
    async sendMessage() {
      if (!this.message.trim()) return
      try {
        const res = await axios.post('http://localhost:5000/chat', {
          message: this.message
        })
        this.response = res.data.response
      } catch (err) {
        this.response = '⚠️ Error connectant amb el servidor.'
        console.error(err)
      }
    }
  }
}
</script>

<style>
.container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 1rem;
  font-family: Arial, sans-serif;
}
textarea {
  width: 100%;
  height: 100px;
  margin-bottom: 1rem;
}
button {
  padding: 0.5rem 1rem;
}
.response {
  margin-top: 1rem;
  background: #f4f4f4;
  padding: 1rem;
  border-radius: 8px;
}
</style>
