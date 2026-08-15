import React from 'react';
import './QuestionCard.css';
import { extractOptionLetter } from '../utils/quizUtils';

const QuestionCard = ({
  question,
  index,
  answers,
  showResults,
  onSelectAnswer,
  onFillBlankAnswer,
  isFillBlankCorrect
}) => {
  const isFillInBlank = (q) => {
    return (
      q?.type === "fillblank" ||
      q?.type === "fill-in-the-blank" ||
      q?.type === "fill" ||
      q?.question?.includes("_______")
    );
  };

  const isFillBlank = isFillInBlank(question);
  const userAnswer = answers[index];

  // The backend's canonical answer identity is the option letter.
  const correctAnswerLetter = extractOptionLetter(
    String(question.correct || '')
  );

  const userAnswerLetter = extractOptionLetter(
    String(userAnswer || '')
  );

  // correct_text is display-only.
  const correctAnswerText =
    question.correct_text ||
    question.correct ||
    '';

  const isCorrect = showResults && (
    isFillBlank
      ? isFillBlankCorrect(index)
      : Boolean(
          userAnswerLetter &&
          userAnswerLetter === correctAnswerLetter
        )
  );
  
  const renderFeedback = () => {
    if (!showResults) return null;
    
    return (
      <div className="sb-feedback-container">
        {question.definition && (
          <div className="sb-feedback-card">
            <span className="sb-feedback-title">Definition</span>
            <p className="sb-feedback-text">{question.definition}</p>
          </div>
        )}
        {question.explanation && (
          <div className="sb-feedback-card">
            <span className="sb-feedback-title">Explanation</span>
            <p className="sb-feedback-text">{question.explanation}</p>
          </div>
        )}
        {question.supporting_fact && (
          <div className="sb-feedback-card">
            <span className="sb-feedback-title">Evidence</span>
            <p className="sb-feedback-text">{question.supporting_fact}</p>
          </div>
        )}
        {question.source_note && (
          <div className="sb-feedback-card">
            <span className="sb-feedback-title">Source</span>
            <p className="sb-feedback-text">{question.source_note}</p>
          </div>
        )}
        {question.related_concepts && question.related_concepts.length > 0 && (
          <div className="sb-feedback-card">
            <span className="sb-feedback-title">Related Concepts</span>
            <div className="sb-related-chips">
              {question.related_concepts.map((concept, i) => (
                <span key={i} className="sb-related-chip">{concept}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

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

      <p className="sb-question-text">{question.question}</p>

      {showResults && !isFillBlank && (
        <div className="sb-correct-answer-banner">
          Correct answer: {correctAnswerText}
        </div>
      )}

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
                Correct answer: {correctAnswerText}
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="sb-options-grid">
          {question.options && question.options.map((option, optIndex) => {
            const letterLabel = String.fromCharCode(65 + optIndex);

            const optionLetter = extractOptionLetter(String(option));

            const isSelected =
              userAnswer === option;

            const isCorrectAnswer =
              showResults &&
              optionLetter === correctAnswerLetter;

            const isWrongAnswer =
              showResults &&
              isSelected &&
              optionLetter !== correctAnswerLetter;

            const isRevealedCorrectAnswer =
              showResults &&
              !isSelected &&
              optionLetter === correctAnswerLetter;

            return (
              <button
                key={optIndex}
                className={`
                  sb-option-btn
                  ${isSelected ? 'sb-option-btn--selected' : ''}
                  ${isCorrectAnswer ? 'sb-option-btn--correct' : ''}
                  ${isWrongAnswer ? 'sb-option-btn--wrong' : ''}
                  ${isRevealedCorrectAnswer ? 'sb-option-btn--reveal' : ''}
                `}
                onClick={() => onSelectAnswer(index, option)}
                disabled={showResults}
                aria-label={`Option ${letterLabel}: ${option}`}
              >
                <span className="sb-option-letter">
                  {letterLabel}
                </span>

                <span className="sb-option-text">
                  {option.replace(/^[A-D]\s*[\)\.\-\s]/, '')}
                </span>
              </button>
            );
          })}
        </div>
      )}
      {renderFeedback()}
    </div>
  );
};

export default QuestionCard;
