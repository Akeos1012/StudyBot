import { useCallback, useEffect, useState } from 'react';
import { knowledgeApi } from '../services/knowledge_api';

export const useKnowledgeTopics = () => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState({ totalTopics: 0, totalNotes: 0, totalFacts: 0, lastUpdated: '' });

  const fetchTopics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await knowledgeApi.getTopics();
      console.log('Knowledge hook data', data);
      setTopics(data.topics || []);
      setSummary({
        totalTopics: data.totalTopics || 0,
        totalNotes: data.totalNotes || 0,
        totalFacts: data.totalFacts || 0,
        lastUpdated: data.lastUpdated || ''
      });
    } catch (err) {
      console.error('Knowledge hook error', err);
      setError(err?.message || 'Unable to load knowledge topics.');
      setTopics([]);
      setSummary({ totalTopics: 0, totalNotes: 0, totalFacts: 0, lastUpdated: '' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopics();
  }, [fetchTopics]);

  return { topics, loading, error, summary, refresh: fetchTopics };
};
