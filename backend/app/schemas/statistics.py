from pydantic import BaseModel


class StreakInfo(BaseModel):
    current: int
    longest: int
    total_days: int


class YearlyPoint(BaseModel):
    year: str
    books: int


class OverallStats(BaseModel):
    books_completed: int
    hours_listened: float
    avg_books_per_month: float
    unique_authors: int
    streak: StreakInfo
    by_year: list[YearlyPoint]


class MonthlyPoint(BaseModel):
    month: str  # "YYYY-MM"
    books: int


class AuthorCount(BaseModel):
    name: str
    books: int


class GenreCount(BaseModel):
    name: str
    books: int


class YearlyStats(BaseModel):
    year: str
    books_in_year: int
    monthly_chart: list[MonthlyPoint]
    top_authors: list[AuthorCount]
    top_narrators: list[AuthorCount]
    genre_breakdown: list[GenreCount]


class BookSummary(BaseModel):
    id: str
    title: str
    author: str
    duration: float  # seconds


class ReadDuration(BaseModel):
    id: str
    title: str
    days: float


class RecapStats(BaseModel):
    year: str
    books_finished: int
    hours_listened: float
    hours_of_content: float
    active_months: int
    top_authors: list[AuthorCount]
    longest_book: BookSummary | None = None
    shortest_book: BookSummary | None = None
    fastest_read: ReadDuration | None = None
    slowest_read: ReadDuration | None = None
    monthly_pace: list[MonthlyPoint]
    top_series: list[GenreCount]


class HeatmapPoint(BaseModel):
    date: str  # "YYYY-MM-DD"
    minutes: int


class HeatmapData(BaseModel):
    year: str
    data: list[HeatmapPoint]


class ListeningHabitCell(BaseModel):
    """Listening attributed to the local timestamp of each ABS session."""

    weekday: int  # Monday is 0
    hour: int  # local hour, 0-23
    minutes: int
    sessions: int


class SessionDurationBin(BaseModel):
    label: str
    sessions: int


class SessionHabitSummary(BaseModel):
    qualifying_sessions: int
    average_minutes: float | None = None
    median_minutes: float | None = None
    sessions_per_active_day: float | None = None
    longest_session_minutes: float | None = None


class ListeningCadence(BaseModel):
    active_days: int
    total_days: int
    active_day_percentage: float | None = None


class ListeningHabits(BaseModel):
    year: str
    timezone: str
    weekday_hour: list[ListeningHabitCell]
    peak: ListeningHabitCell | None = None
    session_summary: SessionHabitSummary
    duration_distribution: list[SessionDurationBin]
    cadence: ListeningCadence


class CompletionVelocityMonth(BaseModel):
    month: str  # "YYYY-MM"
    qualifying_books: int
    median_days: float | None = None


class CompletionVelocity(BaseModel):
    year: str
    qualifying_books: int
    median_days: float | None = None
    monthly_trend: list[CompletionVelocityMonth]


class MonthlyComparisonPoint(BaseModel):
    month: str  # "YYYY-MM"
    books_completed: int
    listening_hours: float


class MonthlyComparison(BaseModel):
    year: str
    timezone: str
    monthly: list[MonthlyComparisonPoint]


class BookLengthBucket(BaseModel):
    label: str
    completed_books: int
    pace_qualifying_books: int
    median_days_to_finish: float | None = None


class BookLengthPreferences(BaseModel):
    year: str
    timezone: str
    qualifying_books: int
    median_duration_hours: float | None = None
    distribution: list[BookLengthBucket]


class GoalForecast(BaseModel):
    year: int
    has_goal: bool
    eligible: bool = False
    target_books: int | None = None
    books_completed: int = 0
    trailing_30_day_completions: int = 0
    projected_books: float | None = None
    required_books_per_week: float | None = None
    ineligibility_reason: str | None = None


class BacklogHealth(BaseModel):
    unstarted_books: int
    in_progress_books: int
    completed_books: int
    partially_started_books: int
    unstarted_remaining_hours: float
    in_progress_remaining_hours: float
    total_remaining_hours: float
    unstarted_duration_books: int
    in_progress_duration_books: int


class SeriesProgress(BaseModel):
    name: str
    completed_books: int
    remaining_books: int
    remaining_hours: float
    remaining_duration_books: int


class AffinityPerson(BaseModel):
    name: str
    available_books: int
    completed_books: int
    completion_rate: float
    listened_hours: float


class AuthorNarratorAffinity(BaseModel):
    authors: list[AffinityPerson]
    narrators: list[AffinityPerson]


class GenreCompletionCorrelation(BaseModel):
    name: str
    known_progress_books: int
    started_or_completed_books: int
    completed_books: int
    completion_rate: float
    pace_qualifying_books: int
    median_days_to_finish: float | None = None


class DurationCompletionPoint(BaseModel):
    id: str
    title: str
    duration_hours: float
    days_to_finish: float


class DurationCompletionCorrelation(BaseModel):
    year: str
    qualifying_books: int
    points: list[DurationCompletionPoint]
    correlation_coefficient: float | None = None
    correlation_method: str | None = None
    direction: str | None = None


class ExtraListeningBook(BaseModel):
    id: str
    title: str
    author: str
    duration_hours: float
    listened_hours: float
    listening_ratio: float


class ExtraListening(BaseModel):
    year: str
    qualifying_books: int
    books: list[ExtraListeningBook]


class StatisticBook(BaseModel):
    id: str
    title: str
    author: str
    finished_at: int | None = None
    duration: float
    time_listening: float


class ListeningBook(BaseModel):
    id: str | None = None
    title: str
    author: str
    minutes: int


class ListeningDay(BaseModel):
    date: str
    minutes: int
    books: list[ListeningBook]


class StatisticsDetail(BaseModel):
    year: str
    books: list[StatisticBook]
    listening_days: list[ListeningDay]
