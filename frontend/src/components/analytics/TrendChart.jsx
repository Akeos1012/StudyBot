import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AnalyticsCard } from './AnalyticsComponents';

const TrendChart = ({ data }) => (
  <AnalyticsCard title="Learning Trend">
    <div className="h-64">
      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="accuracy" stroke="#8884d8" />
            <Line type="monotone" dataKey="mastery" stroke="#82ca9d" />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-gray-500">Not enough data for trend analysis.</p>
      )}
    </div>
  </AnalyticsCard>
);

export default TrendChart;
