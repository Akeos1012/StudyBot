# Frontend Screen Specification

## 1. Dashboard / Home
- **Purpose**: Learning overview and entry point.
- **Backend Services**: `AnalyticsService`
- **APIs**: `/analytics/mastery`, `/analytics/progress`
- **Components**: ActivityFeed, QuickActions, MasterySummary
- **Loading State**: Skeleton loader for charts/cards.
- **Empty State**: Call-to-action to import/process notes.
- **Error State**: "Failed to load dashboard. Please refresh."

## 2. Knowledge Library
- **Purpose**: Explore Obsidian knowledge.
- **Backend Services**: `RagService`
- **APIs**: `/refresh-notes`
- **Components**: FolderBrowser, TopicList, ExtractionStatusCard.
- **Loading State**: Spinner during note refresh.
- **Empty State**: "No notes found. Please configure the Obsidian vault."
- **Error State**: "Refresh failed: [Error Message]"

## 3. Quiz Interface
- **Purpose**: Main learning experience.
- **Architecture**: **Backend-Managed Session** (New Implementation Requirement).
- **Session Flow**: 
    1. UI calls `/quiz/generate`.
    2. Backend creates a session (implicit or explicit) and returns questions.
    3. UI tracks `currentQuestionIndex` and `answers` locally.
    4. Submission uses `/quiz/submit-answer` per question or batch.
- **Persistence**: Page refresh *must* fetch active session or start a new one based on state.
- **Components**: QuestionCard, OptionList, ExplanationBox, ProgressTracker.

## 4. Smart Reviewer
- **Purpose**: Review mistakes/weak concepts.
- **Architecture**: **Option A** (Navigate to Quiz with filters).
- **Review Session Flow**: 
    1. Retrieve weak concepts via `/analytics/weak-topics`.
    2. Display concept-based review card.
    3. "Practice Again" triggers `navigate('/quiz', { state: { topic: concept } })`.
- **Components**: WeakConceptCard, ExplanationCard, RelatedConceptList.

## 5. AI Tutor
- **Purpose**: Explain notes only.
- **Flow**: Chat interface with clear "Grounding" indicators.
- **Components**: ChatWindow, CitationDisplay, GroundingDisclaimer.
- **Required Communication**: Clearly display: "Answers generated from your notes."

## 6. Adaptive Learning
- **Purpose**: Show difficulty progression.
- **APIs**: `/analytics/mastery`
- **Components**: DifficultyChart, ExplanationModal.
- **Logic**: UI maps numerical difficulty (1-5) to human-readable explanations (e.g., "Increased difficulty due to 5 consecutive correct answers").

## 7. Analytics Dashboard
- **Purpose**: Visualize progress.
- **APIs**: `/analytics/mastery`, `/analytics/progress`, `/analytics/weak-topics`, `/analytics/trend`, `/analytics/recommendations`.
- **Components**: MasteryChart, WeakTopicsList, ProgressGraph, RecommendationCards.

## 8. Settings / System Status
- **Purpose**: Backend/Vault/Cache status.
- **APIs**: `/cache/status`
- **Components**: StatusIndicator (Live/Offline), ObsidianPathDisplay.

---

### Final Approval Decision: NOT READY

**Reasoning**: While the backend is mature, the frontend currently manages quiz state locally (`App.jsx`). Moving to the required backend-managed session architecture is a prerequisite for the Quiz and Smart Reviewer features. Knowledge Library needs drag-and-drop or path configuration UI.

### Recommended Implementation Order
1. **Phase 9.1**: Backend-Managed Quiz Session Infrastructure
2. **Phase 9.2**: Quiz UI Refactor (using backend sessions)
3. **Phase 9.3**: Analytics & Dashboard Polish
4. **Phase 9.4**: Knowledge Library UI
5. **Phase 9.5**: Smart Reviewer & AI Tutor
