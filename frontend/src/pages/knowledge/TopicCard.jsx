import React from 'react';

export const TopicCard = ({ topic, selected, onSelect }) => {
  return (
    <button
      type="button"
      className={`sb-topic-card ${selected ? 'sb-topic-card--active' : ''}`}
      onClick={() => onSelect(topic)}
    >
      <div className="sb-topic-card-title-row">
        <span className="sb-topic-card-icon">📚</span>
        <span className="sb-topic-card-name">{topic.name}</span>
      </div>
      <div className="sb-topic-card-meta">
        <span>Notes: {topic.noteCount}</span>
        <span>Facts: {topic.factCount}</span>
      </div>
      <div className="sb-topic-card-status">{topic.status}</div>
    </button>
  );
};

export default TopicCard;
