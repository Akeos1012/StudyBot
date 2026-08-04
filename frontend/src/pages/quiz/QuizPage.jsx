import React from 'react';
import { useQuizSession } from '../../hooks/useQuizSession';

export const QuizPage = ({ userId }) => {
    const { session, loading, error, createQuizSession, submitAnswer, completeSession } = useQuizSession(userId);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    if (!session) {
        return (
            <div>
                <button onClick={() => createQuizSession('Python', 'medium', 5)}>Start Python Quiz</button>
            </div>
        );
    }

    if (session.status === 'completed') {
        return <div>Quiz Completed!</div>;
    }

    return (
        <div>
            <h1>Quiz: {session.topic}</h1>
            <p>Progress: {session.progress?.answered || 0} / {session.progress?.total || 0}</p>
            {/* Render QuestionCard here */}
            <button onClick={completeSession}>Complete Quiz</button>
        </div>
    );
};
