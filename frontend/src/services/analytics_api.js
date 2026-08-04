const API_URL = 'http://localhost:8000';

export const analyticsApi = {
  async _fetch(endpoint, userId) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        'X-User-ID': userId,
      },
    });
    if (!response.ok) throw new Error(`Analytics API error: ${response.statusText}`);
    return response.json();
  },

  async getMastery(userId) {
    return this._fetch('/analytics/mastery', userId);
  },

  async getProgress(userId) {
    return this._fetch('/analytics/progress', userId);
  },

  async getWeakTopics(userId) {
    return this._fetch('/analytics/weak-topics', userId);
  },

  async getSummary(userId) {
    return this._fetch('/analytics/summary', userId);
  },

  async getTrend(userId, days = 30) {
    return this._fetch(`/analytics/trend?days=${days}`, userId);
  },

  async getRecommendations(userId) {
    return this._fetch('/analytics/recommendations', userId);
  },
};
