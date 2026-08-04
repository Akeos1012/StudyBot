import React from 'react';
import { AnalyticsCard } from './AnalyticsComponents';

const ProgressSummary = ({ data }) => (
  <AnalyticsCard title="Progress Summary">
    <div className="text-3xl font-bold text-green-600">{data?.accuracy_percentage ?? 0}%</div>
    <div className="text-sm text-gray-500 mt-2">
      <p>Total Questions: {data?.total_questions_answered ?? 0}</p>
      <p>Correct: {data?.correct_answers ?? 0}</p>
    </div>
  </AnalyticsCard>
);

export default ProgressSummary;
