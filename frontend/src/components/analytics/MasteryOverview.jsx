import React from 'react';
import { AnalyticsCard } from './AnalyticsComponents';

const MasteryOverview = ({ data }) => (
  <AnalyticsCard title="Mastery Overview">
    <div className="text-3xl font-bold text-blue-600">{data?.overall_mastery ?? 0}%</div>
    <div className="text-sm text-gray-500 mt-2">
      <p>Total Attempts: {data?.total_attempts ?? 0}</p>
      <p>Concepts Tracked: {data?.concepts_tracked ?? 0}</p>
    </div>
  </AnalyticsCard>
);

export default MasteryOverview;
