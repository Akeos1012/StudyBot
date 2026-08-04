import React from 'react';
import { analyticsApi } from '../../services/analytics_api';
import { userService } from '../../services/user_service';
import MasteryOverview from '../../components/analytics/MasteryOverview';
import ProgressSummary from '../../components/analytics/ProgressSummary';
import WeakTopicList from '../../components/analytics/WeakTopicList';
import TrendChart from '../../components/analytics/TrendChart';
import ActivityChart from '../../components/analytics/ActivityChart';
import RecommendationList from '../../components/analytics/RecommendationList';
import { LoadingState, ErrorState } from '../../components/analytics/AnalyticsComponents';

const AnalyticsDashboard = () => {
  const [summary, setSummary] = React.useState(null);
  const [trend, setTrend] = React.useState(null);
  const [recommendations, setRecommendations] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const userId = userService.getUserId();
    Promise.all([
      analyticsApi.getSummary(userId),
      analyticsApi.getTrend(userId),
      analyticsApi.getRecommendations(userId)
    ])
      .then(([summaryData, trendData, recData]) => {
        setSummary(summaryData);
        setTrend(trendData);
        setRecommendations(recData.recommendations);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Learning Analytics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <MasteryOverview data={summary?.mastery} />
        <ProgressSummary data={summary?.progress} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <WeakTopicList topics={summary?.weak_topics} />
        <RecommendationList recommendations={recommendations} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TrendChart data={trend?.trend} />
        <ActivityChart />
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
