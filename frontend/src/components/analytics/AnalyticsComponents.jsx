import React from 'react';

export const AnalyticsCard = ({ title, children }) => (
  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
    <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
    {children}
  </div>
);

export const LoadingState = () => (
  <div className="text-center py-4">Loading analytics...</div>
);

export const ErrorState = ({ message }) => (
  <div className="text-red-500 py-4">Error: {message}</div>
);

export const EmptyState = ({ message }) => (
  <div className="text-gray-500 py-4">{message || "No data available."}</div>
);
