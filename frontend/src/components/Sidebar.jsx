import React from 'react';
import './Sidebar.css';

const topicIcons = {
  'AI': '🧠',
  'Algorithms': '📊',
  'Architecture': '🏛️',
  'Cloud': '☁️',
  'Data': '📁',
  'Database': '🗄️',
  'Hardware': '💻',
  'History': '📜',
  'Networking': '🌐',
  'Programming': '💻',
  'Programming Languages': '🔤',
  'Security': '🔒',
  'Software': '📦',
  'Systems': '⚙️'
};

const Sidebar = ({ 
  topics, 
  selectedTopic, 
  onSelectTopic, 
  onGenerateQuiz, 
  loading 
}) => {
  return (
    <aside className="sb-sidebar">
      <div className="sb-sidebar-header">
        <span className="sb-sidebar-title">Topics</span>
        <span className="sb-sidebar-count">{topics.length}</span>
      </div>

      <nav className="sb-sidebar-nav">
        {topics.length === 0 ? (
          <div className="sb-sidebar-empty">
            <div className="sb-sidebar-empty-icon">📚</div>
            <p>No topics yet</p>
            <span>Import a PDF to get started</span>
          </div>
        ) : (
          topics.map((topic) => (
            <button
              key={topic}
              className={`sb-sidebar-item ${selectedTopic === topic ? 'sb-sidebar-item--active' : ''}`}
              onClick={() => onSelectTopic(topic)}
            >
              <span className="sb-sidebar-item-icon">
                {topicIcons[topic] || '📄'}
              </span>
              <span className="sb-sidebar-item-label">{topic}</span>
              {selectedTopic === topic && (
                <span className="sb-sidebar-item-emoji">✦</span>
              )}
            </button>
          ))
        )}
      </nav>

      <div className="sb-sidebar-footer">
        <button
          className="sb-sidebar-generate-btn"
          onClick={onGenerateQuiz}
          disabled={!selectedTopic || loading}
        >
          {loading ? (
            <>
              <span className="sb-spinner" />
              Generating...
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
              Generate Quiz
            </>
          )}
        </button>
        <p className="sb-sidebar-footer-hint">
          {selectedTopic ? (
            <>Selected: <strong>{selectedTopic}</strong></>
          ) : (
            'Select a topic above'
          )}
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;