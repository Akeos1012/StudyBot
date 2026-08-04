import React, { useState, useEffect } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { api } from './services/api';
import { quizApi } from './services/quiz_api';
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import QuizPanel from "./components/QuizPanel";
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard';
import { KnowledgeLibrary } from './pages/knowledge/KnowledgeLibrary';
import { useKnowledgeTopics } from './hooks/useKnowledgeTopics';
import './styles/App.css';

function App() {
  // ... existing state ...
  // ... existing helper functions ...

  const { topics, summary } = useKnowledgeTopics();
  const [selectedTopic, setSelectedTopic] = useState('');
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const generateQuiz = async () => {
    if (!selectedTopic) return;

    setLoading(true);
    setQuestions([]);
    setAnswers({});
    setShowResults(false);

    try {
      const data = await quizApi.createSession(selectedTopic, "medium", 3, "default-user");
      if (data.questions && data.questions.length > 0) {
        setQuestions(data.questions);
      }
    } catch (error) {
      console.error('Error generating quiz:', error);
    }
    setLoading(false);
  };

  const extractLetter = (optionText) => {
    if (!optionText) return '';
    const match = optionText.match(/^([A-D])\s*[\)\.\-\s]/);
    if (match) {
      return match[1];
    }
    const firstChar = optionText.charAt(0);
    if (['A', 'B', 'C', 'D'].includes(firstChar)) {
      return firstChar;
    }
    return '';
  };

  const selectAnswer = (questionIndex, optionText) => {
    if (showResults) return;

    const letter = extractLetter(optionText);
    if (letter) {
      setAnswers(prev => ({
        ...prev,
        [questionIndex]: letter
      }));
    }
  };

  const handleFillBlankAnswer = (questionIndex, value) => {
    if (showResults) return;

    setAnswers(prev => ({
      ...prev,
      [questionIndex]: value
    }));
  };

  const submitQuiz = () => {
    setShowResults(true);
  };

  const calculateScore = () => {
    let correct = 0;
    questions.forEach((q, index) => {
      const userAnswer = String(answers[index] || '').trim().toUpperCase();
      const correctAnswer = String(q.correct || '').trim().toUpperCase();
      if (userAnswer === correctAnswer) {
        correct++;
      }
    });
    return correct;
  };

  const isFillBlankCorrect = (questionIndex) => {
    const q = questions[questionIndex];
    const userAnswer = answers[questionIndex] || '';
    return userAnswer.toLowerCase().trim() === q.correct.toLowerCase().trim();
  };

  const resetQuiz = () => {
    setQuestions([]);
    setAnswers({});
    setShowResults(false);
  };

  return (
    <div className="sb-app">
      <Header
        topicsCount={summary.totalTopics || topics.length}
        questionsCount={questions.length}
      />
      <div className="sb-app-layout">
        <Sidebar
          topics={topics}
          selectedTopic={selectedTopic}
          onSelectTopic={setSelectedTopic}
          onGenerateQuiz={generateQuiz}
          loading={loading}
        />
        <main className="sb-main-content">
          <Routes>
            <Route path="/" element={
              <QuizPanel
                questions={questions}
                loading={loading}
                selectedTopic={selectedTopic}
                answers={answers}
                showResults={showResults}
                onSelectAnswer={selectAnswer}
                onFillBlankAnswer={handleFillBlankAnswer}
                onSubmitQuiz={submitQuiz}
                onResetQuiz={resetQuiz}
                calculateScore={calculateScore}
                isFillBlankCorrect={isFillBlankCorrect}
                extractLetter={extractLetter}
              />
            } />
            <Route path="/analytics" element={<AnalyticsDashboard />} />
            <Route path="/knowledge" element={<KnowledgeLibrary selectedTopic={selectedTopic} onSelectTopic={setSelectedTopic} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;