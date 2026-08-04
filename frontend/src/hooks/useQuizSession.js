import { useState, useEffect, useCallback } from 'react';
import { quizApi } from '../services/quiz_api';

export const useQuizSession = (userId) => {
    const [sessionId, setSessionId] = useState(localStorage.getItem('quiz_session_id'));
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const restoreSession = useCallback(async () => {
        if (!sessionId || !userId) return;
        setLoading(true);
        try {
            const data = await quizApi.getSession(sessionId, userId);
            setSession(data);
        } catch (e) {
            localStorage.removeItem('quiz_session_id');
            setSessionId(null);
            setError('Unable to load quiz. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [sessionId, userId]);

    useEffect(() => {
        restoreSession();
    }, [restoreSession]);

    const createQuizSession = async (topic, difficulty, count) => {
        setLoading(true);
        try {
            const data = await quizApi.createSession(topic, difficulty, count, userId);
            setSessionId(data.session_id);
            localStorage.setItem('quiz_session_id', data.session_id);
            setSession(data);
        } catch (e) {
            setError('Unable to create quiz. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const submitAnswer = async (questionId, answer) => {
        setLoading(true);
        try {
            const result = await quizApi.submitAnswer(sessionId, questionId, answer, userId);
            setSession(prev => ({ ...prev, ...result }));
            return result;
        } catch (e) {
            setError('Failed to submit answer.');
        } finally {
            setLoading(false);
        }
    };

    const completeSession = async () => {
        setLoading(true);
        try {
            const result = await quizApi.completeSession(sessionId, userId);
            setSession(prev => ({ ...prev, status: 'completed', ...result }));
            localStorage.removeItem('quiz_session_id');
        } catch (e) {
            setError('Failed to complete session.');
        } finally {
            setLoading(false);
        }
    };

    return { session, loading, error, createQuizSession, submitAnswer, completeSession };
};
