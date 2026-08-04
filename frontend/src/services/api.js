// API Service - Connects to FastAPI backend

const API_URL = 'http://localhost:8000';


export const api = {

  // Get all topics
  async getTopics() {
    const response = await fetch(
      `${API_URL}/topics`
    );

    return response.json();
  },





  // Generate fill in the blank quiz
  async generateFillBlank(topic, difficulty = "medium") {
    const response = await fetch(
      `${API_URL}/generate-fill-blank`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          topic,
          difficulty,
          fresh: false
        })
      }
    );

    return response.json();
  },


  // Refresh notes
  async refreshNotes() {
    const response = await fetch(
      `${API_URL}/refresh-notes`,
      {
        method: 'POST'
      }
    );

    return response.json();
  }

};