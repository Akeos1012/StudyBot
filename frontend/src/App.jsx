import React, { useState, useEffect } from 'react';
import { api } from './services/api';

function App() {
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  // Load topics on startup
  useEffect(() => {
    api.getTopics()
      .then(data => {
        setTopics(data.topics || []);
      })
      .catch(error => {
        console.error("Failed loading topics:", error);
      });
  }, []);

  // Generate quiz - make ONE API call for 3 questions
  const generateQuiz = async () => {
    if (!selectedTopic) return;
    
    setLoading(true);
    setQuestions([]);
    setAnswers({});
    setShowResults(false);
    
    try {
      const data = await api.generateQuiz({
        topic: selectedTopic,
        count: 3,
        difficulty: "medium",
        fresh: false
      });
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
    // Handle: "A) Memoization", "A. Memoization", "A - Memoization", "A Memoization"
    const match = optionText.match(/^([A-D])\s*[\)\.\-\s]/);
    if (match) {
      return match[1];
    }
    // Fallback: just take first character if it's A-D
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

  // Handle fill-in-the-blank answer
  const handleFillBlankAnswer = (questionIndex, value) => {
    if (showResults) return;
    
    setAnswers(prev => ({
      ...prev,
      [questionIndex]: value
    }));
  };

  // Submit quiz
  const submitQuiz = () => {
    setShowResults(true);
  };

  const calculateScore = () => {
    let correct = 0;

    questions.forEach((q, index) => {
      const userAnswer = String(answers[index] || '')
        .trim()
        .toUpperCase();

      const correctAnswer = String(q.correct || '')
        .trim()
        .toUpperCase();

      if (userAnswer === correctAnswer) {
        correct++;
      }
    });

    return correct;
  };

  // Check if answer is correct for fill-in-the-blank
  const isFillBlankCorrect = (questionIndex) => {
    const q = questions[questionIndex];
    const userAnswer = answers[questionIndex] || '';
    return userAnswer.toLowerCase().trim() === q.correct.toLowerCase().trim();
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navbar */}
      <nav className="bg-white shadow-lg border-b border-indigo-100">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="text-3xl">📚</div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              AI Study Companion
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              {topics.length} topics loaded
            </span>
            <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              🧠 {questions.length} questions
            </span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Topic Selection Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-indigo-50">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <span className="mr-2">🎯</span> Choose a Topic
          </h2>
          
          <div className="flex flex-wrap gap-2 mb-6">
            {topics.map((topic) => (
              <button
                key={topic}
                onClick={() => setSelectedTopic(topic)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                  selectedTopic === topic
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:scale-105'
                }`}
              >
                {topic}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={generateQuiz}
              disabled={!selectedTopic || loading}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                <>
                  <span className="mr-2">🚀</span> Generate Quiz
                </>
              )}
            </button>
            
            {selectedTopic && !loading && (
              <span className="text-sm text-gray-500">
                Generating 3 questions about <span className="font-semibold text-gray-700">{selectedTopic}</span>
              </span>
            )}
          </div>
        </div>

        {/* Quiz Questions */}
        {questions.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-indigo-50">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                <span className="mr-2">📝</span> Quiz
              </h2>
              <button
                onClick={submitQuiz}
                disabled={showResults}
                className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {showResults ? 'Completed ✅' : 'Submit Quiz'}
              </button>
            </div>

            {questions.map((q, index) => {
              const isFillBlank = q.type === 'fillblank' || (q.question && q.question.includes('_______'));
              
              return (
                <div key={index} className="mb-8 p-6 border border-gray-200 rounded-xl hover:shadow-md transition-all duration-200">
                  <div className="flex items-start mb-4">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-sm font-bold mr-3 flex-shrink-0">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-lg font-medium text-gray-800">{q.question}</p>
                      {/* ============ NEW: Fallback badge ============ */}
                    </div>
                  </div>
                  
                  <div className="space-y-2 ml-11">
                    {isFillBlank ? (
                      // Fill-in-the-blank input
                      <div>
                        <input
                          type="text"
                          value={answers[index] || ''}
                          onChange={(e) => handleFillBlankAnswer(index, e.target.value)}
                          disabled={showResults}
                          placeholder="Type your answer..."
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200 disabled:bg-gray-100"
                        />
                        {showResults && (
                          <div className={`mt-2 p-3 rounded-lg ${
                            isFillBlankCorrect(index) ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                          }`}>
                            <p className={`font-semibold ${
                              isFillBlankCorrect(index) ? 'text-green-700' : 'text-red-700'
                            }`}>
                              {isFillBlankCorrect(index) ? '✅ Correct!' : `❌ Incorrect. Answer: ${q.correct}`}
                            </p>
                            <p className="text-gray-700 mt-1">
                              <span className="font-medium">💡 Explanation:</span> {q.explanation}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      // Multiple choice options
                      q.options && q.options.map((option) => {
                        const letter = extractLetter(option);
                        const isSelected = answers[index] === letter;
                        const isCorrect = showResults && letter === q.correct;
                        const isWrong = showResults && isSelected && letter !== q.correct;
                        
                        return (
                          <button
                            key={option}
                            onClick={() => selectAnswer(index, option)}
                            disabled={showResults}
                            className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all duration-200 ${
                              isSelected ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                            } ${
                              isCorrect ? 'border-green-500 bg-green-50 shadow-md' : ''
                            } ${
                              isWrong ? 'border-red-500 bg-red-50 shadow-md' : ''
                            }`}
                          >
                            <span className="font-medium">{option}</span>
                            {showResults && isCorrect && <span className="ml-2 text-green-600">✅</span>}
                            {showResults && isWrong && <span className="ml-2 text-red-600">❌</span>}
                          </button>
                        );
                      })
                    )}
                  </div>

                  {showResults && !isFillBlank && (
                    <>
                      <div className={`mt-4 ml-11 p-4 rounded-xl ${
                        String(answers[index]).toUpperCase() === String(q.correct).toUpperCase() ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                      }`}>
                        <div className="flex items-start">
                          <span className="text-lg mr-2">
                            {String(answers[index]).toUpperCase() === String(q.correct).toUpperCase() ? '✅' : '❌'}
                          </span>
                          <div>
                            <p className={`font-semibold ${
                              String(answers[index]).toUpperCase() === String(q.correct).toUpperCase() ?'text-green-700' : 'text-red-700'
                            }`}>
                              {String(answers[index]).toUpperCase() === String(q.correct).toUpperCase()
                                ? 'Correct!' : `Incorrect. Answer: ${q.correct}`}
                            </p>
                            <p className="text-gray-700 mt-1">
                              <span className="font-medium">💡 Explanation:</span> {q.explanation}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Source Note */}
                      {q.supporting_fact && (
                        <div className="mt-2 ml-11 text-xs text-gray-400 border-t border-gray-100 pt-2">
                          📖 Source Fact: {q.supporting_fact}
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            })}

            {showResults && (
              <div className="mt-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl text-center border border-blue-200">
                <div className="text-5xl font-bold text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text">
                  {calculateScore()} / {questions.length}
                </div>
                <p className="text-gray-600 mt-2">Your Score</p>
                <button
                  onClick={() => {
                    setQuestions([]);
                    setAnswers({});
                    setShowResults(false);
                  }}
                  className="mt-4 px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-200"
                >
                  🔄 New Quiz
                </button>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && questions.length === 0 && selectedTopic && (
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center border border-indigo-50">
            <div className="text-6xl mb-4">🧠</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Ready to learn?</h3>
            <p className="text-gray-500">
              Click <span className="font-semibold text-blue-600">"Generate Quiz"</span> to create questions about <span className="font-semibold text-gray-700">{selectedTopic}</span>
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="text-center py-6 text-sm text-gray-500 border-t border-indigo-100 bg-white/50">
        <p>Built with ❤️ using React, FastAPI, and Ollama</p>
      </footer>
    </div>
  );
}

export default App;