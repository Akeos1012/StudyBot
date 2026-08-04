import React from 'react';
import TopicCard from './TopicCard';

export const TopicList = ({ topics, selectedTopic, onSelectTopic, loading }) => {
  if (loading) {
    return (
      <div className="sb-topic-list sb-topic-list--loading" role="status" aria-live="polite">
        <div className="sb-topic-card sb-topic-card--skeleton" />
        <div className="sb-topic-card sb-topic-card--skeleton" />
        <div className="sb-topic-card sb-topic-card--skeleton" />
      </div>
    );
  }

  if (!topics.length) {
    return (
      <div className="sb-empty-state" role="status">
        <h3>No topics found.</h3>
        <p>Configure your Obsidian vault and refresh knowledge.</p>
      </div>
    );
  }

  return (
    <div className="sb-topic-list">
      {topics.map((topic) => (
        <TopicCard
          key={topic.id || topic.name}
          topic={topic}
          selected={selectedTopic === topic.name}
          onSelect={onSelectTopic}
        />
      ))}
    </div>
  );
};

export default TopicList;
