// API Service - Connects to FastAPI backend
const API_URL = 'http://localhost:8000';

export const api = {
  // Get all topics
  async getTopics() {
    const response = await fetch(`${API_URL}/topics`);
    return response.json();
  },

  // Generate a quiz
  async generateQuiz(topic, count = 5) {
    const response = await fetch(`${API_URL}/generate-quiz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, count })
    });
    return response.json();
  },

  // Refresh notes
  async refreshNotes() {
    const response = await fetch(`${API_URL}/refresh-notes`, {
      method: 'POST'
    });
    return response.json();
  }
};