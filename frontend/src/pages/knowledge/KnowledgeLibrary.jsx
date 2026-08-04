import React from 'react';
import { useKnowledgeTopics } from '../../hooks/useKnowledgeTopics';
import TopicList from './TopicList';
import KnowledgeStatus from './KnowledgeStatus';

export const KnowledgeLibrary = ({ selectedTopic, onSelectTopic }) => {
  const { topics, loading, error, summary, refresh } = useKnowledgeTopics();

  return (
    <div className="sb-knowledge-library">
      <div className="sb-knowledge-library-header">
        <div>
          <h1>Knowledge Library</h1>
          <p>Browse backend-backed topics discovered from your knowledge base.</p>
        </div>
        <button type="button" className="sb-knowledge-refresh" onClick={refresh}>
          Refresh
        </button>
      </div>

      <KnowledgeStatus summary={summary} />

      {error ? (
        <div className="sb-error-state" role="alert">
          <p>{error}</p>
          <button type="button" className="sb-knowledge-refresh" onClick={refresh}>
            Retry
          </button>
        </div>
      ) : (
        <TopicList
          topics={topics}
          selectedTopic={selectedTopic}
          onSelectTopic={onSelectTopic}
          loading={loading}
        />
      )}
    </div>
  );
};

export default KnowledgeLibrary;
