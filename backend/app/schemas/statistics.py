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
