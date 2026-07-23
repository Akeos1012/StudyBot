import React from 'react';
import QuestionCard from './QuestionCard';
import './QuizPanel.css';

const QuizPanel = ({
  questions,
  loading,
  selectedTopic,
  answers,
  showResults,
  onSelectAnswer,
  onFillBlankAnswer,
  onSubmitQuiz,
  onResetQuiz,
  calculateScore,
  isFillBlankCorrect,
  extractLetter
}) => {
  // Render empty state
  if (!loading && questions.length === 0) {
    return (
      <div className="sb-panel sb-panel--empty">
        <div className="sb-empty-state">
          <div className="sb-empty-state-icon">📚</div>
          <h2 className="sb-empty-state-title">Ready to Study?</h2>
          <p className="sb-empty-state-desc">
            Select a topic from the sidebar and generate a quiz.
          </p>
          {selectedTopic && (
            <p className="sb-empty-state-hint">
              Current topic: <strong>{selectedTopic}</strong>
            </p>
          )}
        </div>
      </div>
    );
  }

  // Render loading state
  if (loading) {
    return (
      <div className="sb-panel sb-panel--loading">
        <div className="sb-loading-state">
          <div className="sb-spinner sb-spinner--large" />
          <p className="sb-loading-text">Generating your quiz...</p>
          <p className="sb-loading-sub">This may take a moment</p>
        </div>
      </div>
    );
  }

  // Render quiz
  const score = calculateScore();

  return (
    <div className="sb-panel">
      <div className="sb-panel-header">
        <div className="sb-panel-header-left">
          <h2 className="sb-panel-title">Quiz</h2>
          {selectedTopic && (
            <span className="sb-panel-topic">{selectedTopic}</span>
          )}
        </div>
        <span className="sb-panel-count">{questions.length} questions</span>
      </div>

      <div className="sb-panel-body">
        {questions.map((q, index) => (
          <QuestionCard
            key={index}
            question={q}
            index={index}
            answers={answers}
            showResults={showResults}
            onSelectAnswer={onSelectAnswer}
            onFillBlankAnswer={onFillBlankAnswer}
            isFillBlankCorrect={isFillBlankCorrect}
            extractLetter={extractLetter}
          />
        ))}
      </div>

      <div className="sb-panel-footer">
        {!showResults ? (
          <button
            className="sb-submit-btn"
            onClick={onSubmitQuiz}
            disabled={Object.keys(answers).length < questions.length}
          >
            Submit Quiz
          </button>
        ) : (
          <div className="sb-results-container">
            <div className="sb-score-card">
              <div className="sb-score-number">
                {score}/{questions.length}
              </div>
              <div className="sb-score-label">Correct</div>
              <div className="sb-score-percentage">
                {Math.round((score / questions.length) * 100)}%
              </div>
              <div className="sb-score-bar">
                <div 
                  className="sb-score-bar-fill" 
                  style={{ width: `${(score / questions.length) * 100}%` }}
                />
              </div>
              <div className="sb-score-message">
                {score === questions.length 
                  ? '🎉 Perfect score! Excellent work!' 
                  : score >= questions.length * 0.7 
                    ? '👏 Good job! Keep practicing!' 
                    : '📚 Keep studying! You\'ll improve!'}
              </div>
            </div>
            <button
              className="sb-reset-btn"
              onClick={onResetQuiz}
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizPanel;