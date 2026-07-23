import React from 'react';
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
  const isFillInBlank = (question) => {
    return (
      question?.type === "fillblank" ||
      question?.type === "fill-in-the-blank" ||
      question?.type === "fill" ||
      question?.question?.includes("_______")
    );
  };

  const renderQuestion = (q, index) => {
    const isFillBlank = isFillInBlank(q);
    const userAnswer = answers[index];
    const isCorrect = showResults && isFillBlank ? isFillBlankCorrect(index) : false;
    const correctAnswer = q.correct;

    return (
      <div key={index} className="sb-question-card">
        <div className="sb-question-header">
          <span className="sb-question-number">Q{index + 1}</span>
          {showResults && (
            <span className={`sb-question-badge ${isCorrect ? 'sb-question-badge--correct' : 'sb-question-badge--incorrect'}`}>
              {isCorrect ? '✅ Correct' : '❌ Incorrect'}
            </span>
          )}
        </div>

        <p className="sb-question-text">{q.question}</p>

        {isFillBlank ? (
          <div className="sb-fill-container">
            <input
              type="text"
              className="sb-fill-input"
              value={userAnswer || ''}
              onChange={(e) => onFillBlankAnswer(index, e.target.value)}
              disabled={showResults}
              placeholder="Type your answer..."
              aria-label={`Answer for question ${index + 1}`}
            />
            {showResults && (
              <div className="sb-fill-feedback">
                <span className="sb-fill-correct-answer">
                  Correct answer: {correctAnswer}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="sb-options-grid">
            {q.options && q.options.map((option, optIndex) => {
              const letter = extractLetter(option);
              const isSelected = userAnswer === letter;
              const isCorrectAnswer = showResults && letter === correctAnswer;
              const isWrongAnswer = showResults && isSelected && letter !== correctAnswer;

              return (
                <button
                  key={optIndex}
                  className={`
                    sb-option-btn
                    ${isSelected ? 'sb-option-btn--selected' : ''}
                    ${showResults && isCorrectAnswer ? 'sb-option-btn--correct' : ''}
                    ${showResults && isWrongAnswer ? 'sb-option-btn--wrong' : ''}
                    ${showResults && !isSelected && letter === correctAnswer ? 'sb-option-btn--reveal' : ''}
                  `}
                  onClick={() => onSelectAnswer(index, option)}
                  disabled={showResults}
                  aria-label={`Option ${letter}: ${option}`}
                >
                  <span className="sb-option-letter">{letter}</span>
                  <span className="sb-option-text">{option.replace(/^[A-D]\s*[\)\.\-\s]/, '')}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  };

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
        {questions.map((q, index) => renderQuestion(q, index))}
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