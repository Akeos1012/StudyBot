# Phase 8.6: Mastery Dashboard Design

## 1. Current Frontend Architecture Analysis
- **Structure**: React components (`components/`) and pages (`pages/`).
- **Styling**: Tailwind CSS + local CSS modules.
- **Service Layer**: `analytics_api.js` centralizes backend communication.
- **Limitation**: Components are currently static; need to shift to data-driven, reusable structures.

## 2. Dashboard Layout Proposal

```text
frontend/src/
  pages/analytics/
    AnalyticsDashboard.jsx (Main container)
  components/analytics/
    MasteryOverview.jsx (Stats)
    ProgressSummary.jsx (Stats)
    WeakTopicList.jsx (List)
    TrendChart.jsx (Line chart)
    ActivityChart.jsx (Bar chart)
    AnalyticsCard.jsx (Wrapper)
```

- **AnalyticsDashboard**: Manages API fetching, loading/error states, and layout composition.
- **AnalyticsCard**: Provides standard styling for all dashboard widgets.
- **Chart Components**: Wrappers for visualization logic using Recharts.

## 3. Chart Library Recommendation
- **Recommendation**: **Recharts**.
- **Reasoning**: Native React integration, extensive documentation, responsive by default, highly customizable, and relatively small bundle size compared to alternatives.

## 4. Data Mapping Design

| API Endpoint | Target Component | Data Transformation |
| :--- | :--- | :--- |
| `/analytics/mastery` | `MasteryOverview` | Format % values. |
| `/analytics/progress` | `ProgressSummary` | Format total/percentage values. |
| `/analytics/weak-topics` | `WeakTopicList` | Map priority levels to CSS classes. |
| `/analytics/trend` | `TrendChart` | Map `date` to X-axis, `accuracy` to Y-axis. |

## 5. UX Design Requirements
- **Mastery Overview**: Highlight card with large percentage.
- **Weak Topics**: List sorted by mastery score (ascending).
- **Trends**: Line chart visualizing mastery/accuracy improvement.
- **Loading/Empty States**: Unified components for all dashboard sections.

## 6. State Management Strategy
- **Strategy**: Local React `useState`/`useEffect` within `AnalyticsDashboard`.
- **Reasoning**: Analytics data is page-specific and doesn't require global state at this stage. Keep the architecture simple.

## 7. Testing Plan
- **Unit Tests**: Test individual components with mock data (e.g., `WeakTopicList` with empty/populated arrays).
- **API Integration Tests**: Verify `AnalyticsDashboard` handles API responses (loading -> success/error/empty).
- **Rendering Tests**: Ensure all cards render without crashing.

## 8. Implementation Roadmap
1. Install Recharts.
2. Implement component wrappers for charts.
3. Integrate data mapping in `AnalyticsDashboard`.
4. Add final verification tests.
