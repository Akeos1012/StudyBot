import React from 'react';
import { AnalyticsCard } from './AnalyticsComponents';

const WeakTopicList = ({ topics }) => (
  <AnalyticsCard title="Weak Topics">
    {topics && topics.length > 0 ? (
      <ul className="divide-y divide-gray-200">
        {topics.map((t, index) => (
          <li key={index} className="py-2 flex justify-between">
            <span className="font-medium">{t.topic}</span>
            <span className={`text-sm font-semibold px-2 rounded ${t.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
              {t.mastery}%
            </span>
          </li>
        ))}
      </ul>
    ) : (
      <p className="text-gray-500">No weak topics identified!</p>
    )}
  </AnalyticsCard>
);

export default WeakTopicList;
