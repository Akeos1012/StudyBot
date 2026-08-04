import React from 'react';

const formatTimestamp = (value) => {
  if (!value) return 'Not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

export const KnowledgeStatus = ({ summary }) => {
  return (
    <div className="glass sb-knowledge-status">
      <div className="sb-knowledge-status-header">
        <h2>Knowledge Overview</h2>
        <p>Live data from the backend knowledge pipeline.</p>
      </div>
      <div className="sb-knowledge-status-grid">
        <div>
          <span className="sb-knowledge-stat-label">Topics</span>
          <strong>{summary.totalTopics}</strong>
        </div>
        <div>
          <span className="sb-knowledge-stat-label">Notes</span>
          <strong>{summary.totalNotes}</strong>
        </div>
        <div>
          <span className="sb-knowledge-stat-label">Facts</span>
          <strong>{summary.totalFacts}</strong>
        </div>
        <div>
          <span className="sb-knowledge-stat-label">Last update</span>
          <strong>{formatTimestamp(summary.lastUpdated)}</strong>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeStatus;
