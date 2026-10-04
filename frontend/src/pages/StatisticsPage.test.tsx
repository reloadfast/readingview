import { render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import {
  AuthorNarratorAffinitySection,
  BacklogHealthSection,
  BookLengthPreferencesSection,
  CompletionVelocitySection,
  DurationCompletionCorrelationSection,
  ExtraListeningSection,
  GenreCompletionCorrelationSection,
  GoalForecastSummary,
  ListeningHabitsSection,
  MonthlyComparisonSection,
  SeriesProgressSection,
} from "./StatisticsPage";

function assertInsightStates({
  loading,
  error,
  empty,
  populated,
  emptyMessage,
  populatedMessage,
}: {
  loading: ReactElement;
  error: ReactElement;
  empty: ReactElement;
  populated: ReactElement;
  emptyMessage: RegExp;
  populatedMessage: RegExp;
}) {
  const { container, rerender } = render(loading);
  expect(container.querySelector(".animate-pulse")).toBeInTheDocument();

  rerender(error);
  expect(within(container).queryAllByText(/could not be loaded/i).length).toBeGreaterThan(0);

  rerender(empty);
  expect(within(container).queryAllByText(emptyMessage).length).toBeGreaterThan(0);

  rerender(populated);
  expect(within(container).queryAllByText(populatedMessage).length).toBeGreaterThan(0);
}

describe("ExtraListeningSection", () => {
  const onBookClick = vi.fn();

  it("renders loading, error, empty, and populated states", () => {
    const { container, rerender } = render(
      <ExtraListeningSection data={undefined} isLoading isError={false} onBookClick={onBookClick} />,
    );
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();

    rerender(<ExtraListeningSection data={undefined} isLoading={false} isError onBookClick={onBookClick} />);
    expect(screen.getByText(/could not be loaded/i)).toBeInTheDocument();

    rerender(
      <ExtraListeningSection
        data={{ year: "2024", qualifying_books: 0, books: [] }}
        isLoading={false}
        isError={false}
        onBookClick={onBookClick}
      />,
    );
    expect(screen.getByText(/no completed books with valid media duration/i)).toBeInTheDocument();

    rerender(
      <ExtraListeningSection
        data={{
          year: "2024",
          qualifying_books: 1,
          books: [{
            id: "book-1",
            title: "A Long Listen",
            author: "Reader",
            duration_hours: 10,
            listened_hours: 13,
            listening_ratio: 130,
          }],
        }}
        isLoading={false}
        isError={false}
        onBookClick={onBookClick}
      />,
    );
    expect(screen.getByRole("button", { name: /a long listen/i })).toBeInTheDocument();
    expect(screen.getByText(/does not necessarily mean you re-listened/i)).toBeInTheDocument();
  });
});

describe("GoalForecastSummary", () => {
  it("renders loading, error, and no-goal states", () => {
    const { container, rerender } = render(
      <GoalForecastSummary data={undefined} isLoading isError={false} />,
    );
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();

    rerender(<GoalForecastSummary data={undefined} isLoading={false} isError />);
    expect(screen.getByText(/goal forecast could not be loaded/i)).toBeInTheDocument();

    rerender(
      <GoalForecastSummary
        data={{
          year: 2024,
          has_goal: false,
          eligible: false,
          books_completed: 0,
          trailing_30_day_completions: 0,
          target_books: null,
          projected_books: null,
          required_books_per_week: null,
          ineligibility_reason: null,
        }}
        isLoading={false}
        isError={false}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("does not show an estimate when ineligible and shows one when eligible", () => {
    const { rerender } = render(
      <GoalForecastSummary
        data={{
          year: 2024,
          has_goal: true,
          eligible: false,
          target_books: 24,
          books_completed: 1,
          trailing_30_day_completions: 0,
          projected_books: null,
          required_books_per_week: null,
          ineligibility_reason: "A forecast needs at least 14 days in the calendar year.",
        }}
        isLoading={false}
        isError={false}
      />,
    );
    expect(screen.getByText(/forecast unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/estimated books by year end/i)).not.toBeInTheDocument();

    rerender(
      <GoalForecastSummary
        data={{
          year: 2024,
          has_goal: true,
          eligible: true,
          target_books: 24,
          books_completed: 4,
          trailing_30_day_completions: 2,
          projected_books: 20.5,
          required_books_per_week: 0.4,
          ineligibility_reason: null,
        }}
        isLoading={false}
        isError={false}
      />,
    );
    expect(screen.getByText(/estimated books by year end/i)).toBeInTheDocument();
    expect(screen.getByText(/trailing 30 days/i)).toBeInTheDocument();
  });
});

describe("statistics insight states", () => {
  const noOp = vi.fn();

  it("renders loading, error, empty, and populated states for listening and pace insights", () => {
    assertInsightStates({
      loading: <ListeningHabitsSection data={undefined} isLoading isError={false} />,
      error: <ListeningHabitsSection data={undefined} isLoading={false} isError />,
      empty: <ListeningHabitsSection data={undefined} isLoading={false} isError={false} />,
      populated: <ListeningHabitsSection
        isLoading={false}
        isError={false}
        data={{
          year: "2024", timezone: "UTC", weekday_hour: [{ weekday: 0, hour: 8, minutes: 30, sessions: 1 }],
          peak: { weekday: 0, hour: 8, minutes: 30, sessions: 1 },
          session_summary: { qualifying_sessions: 1, average_minutes: 30, median_minutes: 30, sessions_per_active_day: 1, longest_session_minutes: 30 },
          duration_distribution: [{ label: "15–29 min", sessions: 1 }],
          cadence: { active_days: 1, total_days: 366, active_day_percentage: 0.3 },
        }}
      />,
      emptyMessage: /no positive-duration listening sessions/i,
      populatedMessage: /when you listen/i,
    });

    assertInsightStates({
      loading: <CompletionVelocitySection data={undefined} isLoading isError={false} onMonthClick={noOp} />,
      error: <CompletionVelocitySection data={undefined} isLoading={false} isError onMonthClick={noOp} />,
      empty: <CompletionVelocitySection data={undefined} isLoading={false} isError={false} onMonthClick={noOp} />,
      populated: <CompletionVelocitySection
        isLoading={false}
        isError={false}
        onMonthClick={noOp}
        data={{ year: "2024", qualifying_books: 1, median_days: 4, monthly_trend: [] }}
      />,
      emptyMessage: /no completed books with valid start and finish dates/i,
      populatedMessage: /median days to finish/i,
    });

    assertInsightStates({
      loading: <MonthlyComparisonSection data={undefined} isLoading isError={false} onMonthClick={noOp} />,
      error: <MonthlyComparisonSection data={undefined} isLoading={false} isError onMonthClick={noOp} />,
      empty: <MonthlyComparisonSection data={undefined} isLoading={false} isError={false} onMonthClick={noOp} />,
      populated: <MonthlyComparisonSection
        isLoading={false}
        isError={false}
        onMonthClick={noOp}
        data={{ year: "2024", timezone: "UTC", monthly: [{ month: "2024-01", books_completed: 1, listening_hours: 2 }] }}
      />,
      emptyMessage: /no completed books or positive-duration listening sessions/i,
      populatedMessage: /monthly breakdown/i,
    });

    assertInsightStates({
      loading: <BookLengthPreferencesSection data={undefined} isLoading isError={false} onBucketClick={noOp} />,
      error: <BookLengthPreferencesSection data={undefined} isLoading={false} isError onBucketClick={noOp} />,
      empty: <BookLengthPreferencesSection data={undefined} isLoading={false} isError={false} onBucketClick={noOp} />,
      populated: <BookLengthPreferencesSection
        isLoading={false}
        isError={false}
        onBucketClick={noOp}
        data={{ year: "2024", timezone: "UTC", qualifying_books: 1, median_duration_hours: 8, distribution: [{ label: "5–9:59 hours", completed_books: 1, pace_qualifying_books: 1, median_days_to_finish: 4 }] }}
      />,
      emptyMessage: /no completed books with a valid media duration/i,
      populatedMessage: /completed-book duration distribution/i,
    });
  });

  it("renders loading, error, empty, and populated states for progress and preference insights", () => {
    const inRouter = (element: ReactElement) => <MemoryRouter>{element}</MemoryRouter>;

    assertInsightStates({
      loading: inRouter(<BacklogHealthSection data={undefined} isLoading isError={false} />),
      error: inRouter(<BacklogHealthSection data={undefined} isLoading={false} isError />),
      empty: inRouter(<BacklogHealthSection data={undefined} isLoading={false} isError={false} />),
      populated: inRouter(<BacklogHealthSection isLoading={false} isError={false} data={{ unstarted_books: 1, in_progress_books: 1, completed_books: 1, partially_started_books: 1, unstarted_remaining_hours: 8, in_progress_remaining_hours: 2, total_remaining_hours: 10, unstarted_duration_books: 1, in_progress_duration_books: 1 }} />),
      emptyMessage: /no library books with qualifying progress data/i,
      populatedMessage: /partially started books/i,
    });

    assertInsightStates({
      loading: inRouter(<SeriesProgressSection data={undefined} isLoading isError={false} />),
      error: inRouter(<SeriesProgressSection data={undefined} isLoading={false} isError />),
      empty: inRouter(<SeriesProgressSection data={undefined} isLoading={false} isError={false} />),
      populated: inRouter(<SeriesProgressSection isLoading={false} isError={false} data={[{ name: "A Series", completed_books: 2, remaining_books: 1, remaining_hours: 5, remaining_duration_books: 1 }]} />),
      emptyMessage: /no series with determinable incomplete books/i,
      populatedMessage: /a series/i,
    });

    const affinityPerson = { name: "A. Author", available_books: 3, completed_books: 2, completion_rate: 66.7, listened_hours: 10 };
    assertInsightStates({
      loading: <AuthorNarratorAffinitySection data={undefined} isLoading isError={false} onAuthorClick={noOp} onNarratorClick={noOp} />,
      error: <AuthorNarratorAffinitySection data={undefined} isLoading={false} isError onAuthorClick={noOp} onNarratorClick={noOp} />,
      empty: <AuthorNarratorAffinitySection data={{ authors: [], narrators: [] }} isLoading={false} isError={false} onAuthorClick={noOp} onNarratorClick={noOp} />,
      populated: <AuthorNarratorAffinitySection data={{ authors: [affinityPerson], narrators: [{ ...affinityPerson, name: "N. Narrator" }] }} isLoading={false} isError={false} onAuthorClick={noOp} onNarratorClick={noOp} />,
      emptyMessage: /no one with at least three library books/i,
      populatedMessage: /a\. author/i,
    });

    assertInsightStates({
      loading: <GenreCompletionCorrelationSection data={undefined} isLoading isError={false} onGenreClick={noOp} />,
      error: <GenreCompletionCorrelationSection data={undefined} isLoading={false} isError onGenreClick={noOp} />,
      empty: <GenreCompletionCorrelationSection data={undefined} isLoading={false} isError={false} onGenreClick={noOp} />,
      populated: <GenreCompletionCorrelationSection data={[{ name: "Fantasy", known_progress_books: 3, started_or_completed_books: 3, completed_books: 2, completion_rate: 66.7, pace_qualifying_books: 2, median_days_to_finish: 4 }]} isLoading={false} isError={false} onGenreClick={noOp} />,
      emptyMessage: /no genres have at least three/i,
      populatedMessage: /fantasy/i,
    });

    assertInsightStates({
      loading: <DurationCompletionCorrelationSection data={undefined} isLoading isError={false} onBookClick={noOp} />,
      error: <DurationCompletionCorrelationSection data={undefined} isLoading={false} isError onBookClick={noOp} />,
      empty: <DurationCompletionCorrelationSection data={undefined} isLoading={false} isError={false} onBookClick={noOp} />,
      populated: <DurationCompletionCorrelationSection data={{ year: "2024", qualifying_books: 1, points: [{ id: "book-1", title: "A Book", duration_hours: 8, days_to_finish: 4 }], correlation_coefficient: null, correlation_method: null, direction: null }} isLoading={false} isError={false} onBookClick={noOp} />,
      emptyMessage: /no completed books with valid duration, start, and finish data/i,
      populatedMessage: /length & completion pace/i,
    });
  });
});
