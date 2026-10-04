import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ExtraListeningSection, GoalForecastSummary } from "./StatisticsPage";

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
