const API_BASE = '/api'; // Assuming proxy setup or relative path
const USER_ID_HEADER = 'X-User-ID';

export const quizApi = {
    async createSession(topic, difficulty, count, userId, excludeIds = []) {
        const response = await fetch(`${API_BASE}/quiz/session/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', [USER_ID_HEADER]: userId },
            body: JSON.stringify({ topic, difficulty, count, exclude_ids: excludeIds })
        });
        if (!response.ok) throw new Error('Failed to create session');
        return response.json();
    },

    async getSession(sessionId, userId) {
        const response = await fetch(`${API_BASE}/quiz/session/${sessionId}`, {
            headers: { [USER_ID_HEADER]: userId }
        });
        if (!response.ok) throw new Error('Failed to fetch session');
        return response.json();
    },

    async submitAnswer(sessionId, questionId, answer, userId) {
        const response = await fetch(`${API_BASE}/quiz/session/${sessionId}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', [USER_ID_HEADER]: userId },
            body: JSON.stringify({ question_id: questionId, answer })
        });
        if (!response.ok) throw new Error('Failed to submit answer');
        return response.json();
    },

    async completeSession(sessionId, userId) {
        const response = await fetch(`${API_BASE}/quiz/session/${sessionId}/complete`, {
            method: 'PATCH',
            headers: { [USER_ID_HEADER]: userId }
        });
        if (!response.ok) throw new Error('Failed to complete session');
        return response.json();
    }
};
