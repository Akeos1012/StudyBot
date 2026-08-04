import React from 'react';
import { AnalyticsCard } from './AnalyticsComponents';

const RecommendationList = ({ recommendations }) => (
  <AnalyticsCard title="Recommendations">
    {recommendations && recommendations.length > 0 ? (
      <ul className="divide-y divide-gray-200">
        {recommendations.map((rec, index) => (
          <li key={index} className="py-3">
            <div className="flex justify-between items-center">
              <span className="font-bold text-lg">{rec.topic}</span>
              <span className={`text-xs font-semibold px-2 py-1 rounded ${rec.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                {rec.priority.toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{rec.reason}</p>
            <p className="text-sm font-medium text-blue-600 mt-1">{rec.suggested_action}</p>
          </li>
        ))}
      </ul>
    ) : (
      <p className="text-gray-500">No recommendations currently available.</p>
    )}
  </AnalyticsCard>
);

export default RecommendationList;
