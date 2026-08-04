const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const normalizeTopic = (topic) => ({
  id: topic.name?.toLowerCase() || '',
  name: topic.name || 'Untitled topic',
  noteCount: Number(topic.note_count || 0),
  factCount: Number(topic.fact_count || 0),
  lastUpdated: topic.last_updated || '',
  status: topic.status || 'ready'
});

export const knowledgeApi = {
  async getTopics() {
    const url = `${API_BASE}/knowledge/topics`;
    console.log('Knowledge API request', url);
    const response = await fetch(url);
    console.log('Knowledge API response', response.status, response.headers.get('content-type'));
    if (!response.ok) {
      throw new Error(`Failed to fetch knowledge topics: ${response.status}`);
    }

    const payload = await response.json();
    console.log('Knowledge API payload', payload);
    const topics = Array.isArray(payload?.topics) ? payload.topics : [];

    const normalizedTopics = topics.map(normalizeTopic);
    const latestTimestamp = normalizedTopics
      .map((topic) => topic.lastUpdated)
      .filter(Boolean)
      .sort()
      .pop() || '';

    return {
      topics: normalizedTopics,
      totalTopics: Number(payload?.total_topics || normalizedTopics.length),
      totalNotes: normalizedTopics.reduce((sum, topic) => sum + topic.noteCount, 0),
      totalFacts: normalizedTopics.reduce((sum, topic) => sum + topic.factCount, 0),
      lastUpdated: latestTimestamp
    };
  }
};
