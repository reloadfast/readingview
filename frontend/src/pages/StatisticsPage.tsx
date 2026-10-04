import { Fragment, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Scatter,
  ScatterChart,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { BookOpen, Clock, TrendingUp, Flame, Pencil, Check, X } from "lucide-react";
import { AbsBookLink, Card, CardContent, Skeleton, Select } from "@/components/ui";
import { useStatistics, useYearlyStats, useRecap, useHeatmap, useListeningHabits, useCompletionVelocity, useMonthlyComparison, useBookLengthPreferences, useGoalForecast, useBacklogHealth, useSeriesProgress, useAuthorNarratorAffinity, useGenreCompletionCorrelation, useDurationCompletionCorrelation, useExtraListening, useStatisticsDetail } from "@/hooks/useStatistics";
import { useGoals, useSetGoal } from "@/hooks/useGoals";
import { formatDuration } from "@/lib/utils";
import type { AffinityPerson, AuthorNarratorAffinity, BacklogHealth, BookLengthPreferences, CompletionVelocity, DurationCompletionCorrelation, ExtraListening, GenreCompletionCorrelation, GoalForecast, MonthlyComparison, RecapStats, AuthorCount, GenreCount, HeatmapPoint, ListeningHabitCell, ListeningHabits, SeriesProgress, StatisticsDetail } from "@/lib/api";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CURRENT_YEAR = new Date().getFullYear();

const YEAR_OPTIONS = [
  { value: "all", label: "All Time" },
  ...Array.from({ length: 5 }, (_, i) => {
    const y = String(CURRENT_YEAR - i);
    return { value: y, label: y };
  }),
];

const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
  "var(--color-chart-6)",
  "var(--color-chart-7)",
  "var(--color-chart-8)",
  "var(--color-chart-9)",
];

const TOOLTIP_STYLE = {
  backgroundColor: "var(--color-surface)",
  border: "1px solid var(--color-border)",
  borderRadius: "8px",
  color: "var(--color-text-primary)",
  fontSize: "13px",
};

const CURSOR_STYLE = { fill: "var(--color-surface-hover)" };

function longestConsecutiveDays(points: HeatmapPoint[]): number {
  const dates = [...new Set(points.map((point) => point.date))].sort();
  let longest = 0;
  let run = 0;
  let previous: Date | undefined;

  for (const date of dates) {
    const current = new Date(`${date}T00:00:00Z`);
    run = previous && current.getTime() - previous.getTime() === 86_400_000 ? run + 1 : 1;
    longest = Math.max(longest, run);
    previous = current;
  }

  return longest;
}

// ---------------------------------------------------------------------------
// Skeletons
// ---------------------------------------------------------------------------

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <Skeleton className="w-9 h-9 rounded-lg flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-8 w-14" />
          <Skeleton className="h-3 w-24" />
        </div>
      </CardContent>
    </Card>
  );
}

function ChartSkeleton({ height = 300 }: { height?: number }) {
  return <Skeleton className="w-full rounded-xl" style={{ height }} />;
}

// ---------------------------------------------------------------------------
// Listening habits
// ---------------------------------------------------------------------------

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function formatMinutes(minutes: number | null | undefined) {
  return minutes === null || minutes === undefined ? "—" : `${minutes % 1 === 0 ? minutes : minutes.toFixed(1)} min`;
}

function ListeningHabitsSection({ data, isLoading, isError }: { data: ListeningHabits | undefined; isLoading: boolean; isError: boolean }) {
  const [selected, setSelected] = useState<ListeningHabitCell | null>(null);

  if (isLoading) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Listening Habits</h2><ChartSkeleton height={260} /></section>;
  }
  if (isError) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Listening Habits</h2><Card><CardContent><p className="text-sm text-destructive">Listening habits could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  }
  if (!data || data.session_summary.qualifying_sessions === 0) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Listening Habits</h2><Card><CardContent><p className="text-sm text-text-secondary">No positive-duration listening sessions are available for this period.</p></CardContent></Card></section>;
  }

  const cellByPosition = new Map(data.weekday_hour.map((cell) => [`${cell.weekday}-${cell.hour}`, cell]));
  const maxMinutes = Math.max(...data.weekday_hour.map((cell) => cell.minutes), 1);
  const inspected = selected ?? data.peak;
  const peakLabel = data.peak ? `${WEEKDAYS[data.peak.weekday]} at ${String(data.peak.hour).padStart(2, "0")}:00` : "—";

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-text-primary">Listening Habits</h2>
        <p className="text-xs text-text-secondary mt-1">Session minutes are attributed to each session’s timestamp in {data.timezone}.</p>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <CardContent className="space-y-4">
            <div className="flex items-baseline justify-between gap-3"><h3 className="font-medium text-text-primary">When you listen</h3><span className="text-xs text-text-secondary">Peak: {peakLabel}</span></div>
            <div className="overflow-x-auto">
              <div className="grid min-w-[640px] grid-cols-[3rem_repeat(24,minmax(1rem,1fr))] gap-1" role="grid" aria-label="Listening minutes by weekday and hour">
                <span />
                {Array.from({ length: 24 }, (_, hour) => <span key={hour} className="text-center text-[10px] text-text-secondary">{hour % 3 === 0 ? hour : ""}</span>)}
                {WEEKDAYS.map((weekday, weekdayIndex) => <Fragment key={weekday}>
                  <span key={`${weekday}-label`} className="self-center text-xs text-text-secondary">{weekday}</span>
                  {Array.from({ length: 24 }, (_, hour) => {
                    const cell = cellByPosition.get(`${weekdayIndex}-${hour}`);
                    const opacity = cell ? Math.max(0.12, cell.minutes / maxMinutes) : 0.05;
                    const label = `${weekday}, ${String(hour).padStart(2, "0")}:00: ${cell?.minutes ?? 0} minutes across ${cell?.sessions ?? 0} sessions`;
                    return <button key={`${weekday}-${hour}`} type="button" role="gridcell" aria-label={label} title={label} onClick={() => setSelected(cell ?? null)} className="aspect-square min-h-4 rounded-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-accent" style={{ backgroundColor: `color-mix(in srgb, var(--color-accent) ${Math.round(opacity * 100)}%, transparent)` }} />;
                  })}
                </Fragment>)}
              </div>
            </div>
            <p className="text-xs text-text-secondary" aria-live="polite">{inspected ? `${WEEKDAYS[inspected.weekday]} at ${String(inspected.hour).padStart(2, "0")}:00 — ${inspected.minutes} minutes across ${inspected.sessions} session${inspected.sessions === 1 ? "" : "s"}.` : "Select a time slot to inspect it."}</p>
            <p className="sr-only">{data.peak ? `Highest listening time is ${peakLabel}, with ${data.peak.minutes} minutes across ${data.peak.sessions} sessions.` : "No listening time is available."}</p>
          </CardContent>
        </Card>
        <div className="grid grid-cols-2 gap-4">
          {[
            ["Average session", formatMinutes(data.session_summary.average_minutes)],
            ["Median session", formatMinutes(data.session_summary.median_minutes)],
            ["Longest session", formatMinutes(data.session_summary.longest_session_minutes)],
            ["Sessions / active day", data.session_summary.sessions_per_active_day ?? "—"],
            ["Active listening days", `${data.cadence.active_days} / ${data.cadence.total_days}`],
            ["Days with activity", data.cadence.active_day_percentage == null ? "—" : `${data.cadence.active_day_percentage}%`],
          ].map(([label, value]) => <Card key={label}><CardContent><p className="text-2xl font-bold text-text-primary">{value}</p><p className="text-xs text-text-secondary mt-1">{label}</p></CardContent></Card>)}
        </div>
      </div>
      <Card><CardContent><h3 className="font-medium text-text-primary mb-3">Session length distribution</h3><div className="grid grid-cols-2 sm:grid-cols-4 gap-3">{data.duration_distribution.map((bin) => <div key={bin.label} className="rounded-lg bg-surface-hover p-3"><p className="text-xl font-bold text-text-primary">{bin.sessions}</p><p className="text-xs text-text-secondary">{bin.label}</p></div>)}</div><p className="text-xs text-text-secondary mt-3">Based on {data.session_summary.qualifying_sessions} positive-duration session{data.session_summary.qualifying_sessions === 1 ? "" : "s"}.</p></CardContent></Card>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Completion velocity
// ---------------------------------------------------------------------------

function CompletionVelocitySection({ data, isLoading, isError, onMonthClick }: { data: CompletionVelocity | undefined; isLoading: boolean; isError: boolean; onMonthClick: (month: string) => void }) {
  if (isLoading) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Completion Pace</h2><ChartSkeleton height={260} /></section>;
  }
  if (isError) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Completion Pace</h2><Card><CardContent><p className="text-sm text-destructive">Completion pace could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  }
  if (!data || data.qualifying_books === 0) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Completion Pace</h2><Card><CardContent><p className="text-sm text-text-secondary">No completed books with valid start and finish dates are available for this period.</p></CardContent></Card></section>;
  }

  const trend = data.monthly_trend.filter((month) => month.median_days !== null);
  const excludedMonths = data.monthly_trend.filter((month) => month.median_days === null);
  return (
    <section className="space-y-4">
      <div><h2 className="text-lg font-semibold text-text-primary">Completion Pace</h2><p className="text-xs text-text-secondary mt-1">Based on {data.qualifying_books} completed book{data.qualifying_books === 1 ? "" : "s"} with valid start and finish dates.</p></div>
      <div className="grid grid-cols-1 lg:grid-cols-[15rem_1fr] gap-6">
        <Card><CardContent><p className="text-3xl font-bold text-text-primary">{data.median_days}d</p><p className="text-sm text-text-secondary mt-1">Median days to finish</p><p className="text-xs text-text-secondary mt-4">This is a representative middle value; fastest and slowest reads are shown separately as outliers.</p></CardContent></Card>
        <Card><CardContent>
          <h3 className="font-medium text-text-primary mb-3">Monthly median days to finish</h3>
          {trend.length ? <>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={trend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} unit="d" />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={CURSOR_STYLE} formatter={(value: number) => [`${value} days`, "Median"]} labelFormatter={(label) => String(label)} />
                <Bar dataKey="median_days" fill="var(--color-chart-2)" radius={[4, 4, 0, 0]} cursor="pointer" onClick={(point) => { const month = (point as { month?: string }).month; if (month) onMonthClick(month); }} />
              </BarChart>
            </ResponsiveContainer>
            <p className="sr-only">Monthly completion pace is shown for {trend.length} month{trend.length === 1 ? "" : "s"} with at least three qualifying completed books. Select a bar to view its completed books.</p>
          </> : <p className="text-sm text-text-secondary py-16 text-center">Monthly pace needs at least three qualifying completed books in a month.</p>}
          {excludedMonths.length > 0 && <p className="text-xs text-text-secondary mt-3">{excludedMonths.length} month{excludedMonths.length === 1 ? " has" : "s have"} fewer than three qualifying completed books and {excludedMonths.length === 1 ? "is" : "are"} omitted from the trend.</p>}
        </CardContent></Card>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  icon: Icon,
  onClick,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  onClick?: () => void;
}) {
  const content = (
    <Card className={onClick ? "h-full transition-colors hover:bg-surface-hover" : "h-full"}>
      <CardContent className="flex items-center gap-4">
        <div className="p-2 rounded-lg bg-accent/10 flex-shrink-0">
          <Icon className="w-5 h-5 text-accent" />
        </div>
        <div>
          <p className="text-3xl font-bold text-text-primary">{value}</p>
          <p className="text-sm text-text-secondary">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
  return onClick ? (
    <button onClick={onClick} className="text-left rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
      {content}
    </button>
  ) : content;
}

function MonthlyComparisonSection({ data, isLoading, isError, onMonthClick }: { data: MonthlyComparison | undefined; isLoading: boolean; isError: boolean; onMonthClick: (month: string, metric: "books" | "hours") => void }) {
  const [metric, setMetric] = useState<"books" | "hours">("books");

  if (isLoading) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Monthly Breakdown</h2><ChartSkeleton /></section>;
  }
  if (isError) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Monthly Breakdown</h2><Card><CardContent><p className="text-sm text-destructive">Monthly comparison could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  }
  const monthly = data?.monthly ?? [];
  if (!monthly.some((point) => point.books_completed > 0 || point.listening_hours > 0)) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Monthly Breakdown</h2><Card><CardContent><p className="text-sm text-text-secondary">No completed books or positive-duration listening sessions are available for this period.</p></CardContent></Card></section>;
  }

  const key = metric === "books" ? "books_completed" : "listening_hours";
  const label = metric === "books" ? "Books completed" : "Listening hours";
  const contrary: { point: (typeof monthly)[number]; previous: (typeof monthly)[number] }[] = [];
  for (let index = 1; index < monthly.length; index += 1) {
    const point = monthly[index];
    const previous = monthly[index - 1];
    if (point && previous && (point.books_completed - previous.books_completed) * (point.listening_hours - previous.listening_hours) < 0) {
      contrary.push({ point, previous });
    }
  }
  const latestContrary = contrary.at(-1);
  const comparisonSummary = latestContrary
    ? `In ${new Date(`${latestContrary.point.month}-01T12:00:00`).toLocaleDateString(undefined, { month: "long", year: "numeric" })}, completed books ${latestContrary.point.books_completed > latestContrary.previous.books_completed ? "increased" : "decreased"} while session listening hours ${latestContrary.point.listening_hours > latestContrary.previous.listening_hours ? "increased" : "decreased"}.`
    : "No month-to-month change in completions moved opposite to listening hours in this period.";

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold text-text-primary">Monthly Breakdown</h2><p className="text-xs text-text-secondary mt-1">Listening hours are summed from positive-duration sessions at their timestamp in {data?.timezone}.</p></div><div className="inline-flex rounded-lg border border-border p-1" role="group" aria-label="Monthly metric"><button type="button" aria-pressed={metric === "books"} onClick={() => setMetric("books")} className={`rounded-md px-3 py-1.5 text-sm ${metric === "books" ? "bg-accent text-white" : "text-text-secondary hover:bg-surface-hover"}`}>Books</button><button type="button" aria-pressed={metric === "hours"} onClick={() => setMetric("hours")} className={`rounded-md px-3 py-1.5 text-sm ${metric === "hours" ? "bg-accent text-white" : "text-text-secondary hover:bg-surface-hover"}`}>Listening hours</button></div></div>
      <Card><CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthly} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis allowDecimals={metric === "hours"} tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={CURSOR_STYLE} formatter={(value: number) => [metric === "hours" ? `${value} hrs` : value, label]} />
            <Bar dataKey={key} fill="var(--color-chart-1)" radius={[4, 4, 0, 0]} maxBarSize={40} cursor="pointer" onClick={(point) => { const month = (point as { month?: string }).month; if (month) onMonthClick(month, metric); }} />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-text-secondary mt-3">{comparisonSummary}</p>
        <p className="sr-only">The chart shows {label.toLowerCase()} for each month. Select a bar to inspect the underlying {metric === "books" ? "completed books" : "listening sessions"}.</p>
      </CardContent></Card>
    </section>
  );
}

function BookLengthPreferencesSection({ data, isLoading, isError, onBucketClick }: { data: BookLengthPreferences | undefined; isLoading: boolean; isError: boolean; onBucketClick: (bucket: string) => void }) {
  if (isLoading) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Book Length Preferences</h2><ChartSkeleton height={220} /></section>;
  }
  if (isError) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Book Length Preferences</h2><Card><CardContent><p className="text-sm text-destructive">Book-length preferences could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  }
  if (!data || data.qualifying_books === 0) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Book Length Preferences</h2><Card><CardContent><p className="text-sm text-text-secondary">No completed books with a valid media duration are available for this period.</p></CardContent></Card></section>;
  }

  return (
    <section className="space-y-4">
      <div><h2 className="text-lg font-semibold text-text-primary">Book Length Preferences</h2><p className="text-xs text-text-secondary mt-1">Median completed-book length: {data.median_duration_hours} hours, based on {data.qualifying_books} completed book{data.qualifying_books === 1 ? "" : "s"}.</p></div>
      <Card><CardContent>
        <h3 className="font-medium text-text-primary mb-3">Completed-book duration distribution</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {data.distribution.map((bucket) => <button key={bucket.label} type="button" onClick={() => onBucketClick(bucket.label)} className="rounded-lg bg-surface-hover p-3 text-left transition-colors hover:bg-accent/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"><p className="text-xl font-bold text-text-primary">{bucket.completed_books}</p><p className="text-xs text-text-secondary">{bucket.label}</p></button>)}
        </div>
        <p className="sr-only">Select a duration bucket to inspect its completed books.</p>
      </CardContent></Card>
      <Card><CardContent>
        <h3 className="font-medium text-text-primary mb-3">Length and completion pace</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {data.distribution.map((bucket) => <button key={bucket.label} type="button" onClick={() => onBucketClick(bucket.label)} className="rounded-lg border border-border p-3 text-left transition-colors hover:bg-surface-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"><p className="text-xl font-bold text-text-primary">{bucket.median_days_to_finish == null ? "—" : `${bucket.median_days_to_finish}d`}</p><p className="text-xs text-text-secondary">Median days · {bucket.label}</p><p className="text-xs text-text-secondary mt-2">{bucket.pace_qualifying_books} with valid start/finish dates</p></button>)}
        </div>
        <p className="text-xs text-text-secondary mt-3">Completion pace excludes books without valid start and finish timestamps.</p>
      </CardContent></Card>
    </section>
  );
}

function BacklogHealthSection({ data, isLoading, isError }: { data: BacklogHealth | undefined; isLoading: boolean; isError: boolean }) {
  if (isLoading) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Backlog Health</h2><div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, index) => <StatCardSkeleton key={index} />)}</div></section>;
  }
  if (isError) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Backlog Health</h2><Card><CardContent><p className="text-sm text-destructive">Backlog health could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  }
  if (!data || data.unstarted_books + data.in_progress_books + data.completed_books === 0) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Backlog Health</h2><Card><CardContent><p className="text-sm text-text-secondary">No library books with qualifying progress data are available.</p></CardContent></Card></section>;
  }
  return (
    <section className="space-y-4">
      <div><h2 className="text-lg font-semibold text-text-primary">Backlog Health</h2><p className="text-xs text-text-secondary mt-1">Current library state; remaining time uses valid media duration and ABS progress only.</p></div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card><CardContent><p className="text-3xl font-bold text-text-primary">{data.unstarted_books}</p><p className="text-sm text-text-secondary">Unstarted books</p></CardContent></Card>
        <Link to="/library" className="rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"><Card className="h-full transition-colors hover:bg-surface-hover"><CardContent><p className="text-3xl font-bold text-accent">{data.partially_started_books}</p><p className="text-sm text-text-secondary">Partially started books</p><p className="text-xs text-accent mt-1">Open library →</p></CardContent></Card></Link>
        <Card><CardContent><p className="text-3xl font-bold text-text-primary">{data.completed_books}</p><p className="text-sm text-text-secondary">Completed books</p></CardContent></Card>
        <Card><CardContent><p className="text-3xl font-bold text-text-primary">{data.total_remaining_hours}</p><p className="text-sm text-text-secondary">Hours remaining</p></CardContent></Card>
      </div>
      <Card><CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm"><div><p className="font-medium text-text-primary">Unstarted: {data.unstarted_remaining_hours} hours</p><p className="text-xs text-text-secondary mt-1">From {data.unstarted_duration_books} unstarted book{data.unstarted_duration_books === 1 ? "" : "s"} with valid duration.</p></div><div><p className="font-medium text-text-primary">In progress: {data.in_progress_remaining_hours} hours</p><p className="text-xs text-text-secondary mt-1">From {data.in_progress_duration_books} partially started book{data.in_progress_duration_books === 1 ? "" : "s"} with valid duration and progress.</p></div></CardContent></Card>
    </section>
  );
}

function SeriesProgressSection({ data, isLoading, isError }: { data: SeriesProgress[] | undefined; isLoading: boolean; isError: boolean }) {
  if (isLoading) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Series Progress</h2><ChartSkeleton height={180} /></section>;
  }
  if (isError) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Series Progress</h2><Card><CardContent><p className="text-sm text-destructive">Series progress could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  }
  if (!data?.length) {
    return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Series Progress</h2><Card><CardContent><p className="text-sm text-text-secondary">No series with determinable incomplete books are available.</p></CardContent></Card></section>;
  }
  return (
    <section className="space-y-4">
      <div><h2 className="text-lg font-semibold text-text-primary">Series Progress</h2><p className="text-xs text-text-secondary mt-1">Closest to finish first: fewest remaining books, then fewest remaining hours.</p></div>
      <Card><CardContent className="divide-y divide-border">
        {data.map((series) => <Link key={series.name} to={`/series/${encodeURIComponent(series.name)}`} className="block py-3 first:pt-0 last:pb-0 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-accent hover:bg-surface-hover"><div className="flex items-start justify-between gap-4"><div><p className="font-medium text-text-primary">{series.name}</p><p className="text-xs text-text-secondary mt-1">{series.completed_books} completed · {series.remaining_books} remaining</p></div><div className="text-right"><p className="text-sm font-medium text-text-primary">{series.remaining_duration_books ? `${series.remaining_hours} hrs` : "—"}</p><p className="text-xs text-text-secondary">{series.remaining_duration_books}/{series.remaining_books} with duration</p></div></div></Link>)}
      </CardContent></Card>
    </section>
  );
}

type AffinitySort = "completion_rate" | "completed_books" | "listened_hours";

function AffinityRanking({ title, people }: { title: string; people: AffinityPerson[] }) {
  if (!people.length) return <p className="py-8 text-center text-sm text-text-secondary">No one with at least three library books qualifies yet.</p>;
  return <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-left text-xs text-text-secondary"><tr><th className="pb-2 font-medium">Name</th><th className="pb-2 font-medium text-right">Finished / available</th><th className="pb-2 font-medium text-right">Rate</th><th className="pb-2 font-medium text-right">Listened</th></tr></thead><tbody className="divide-y divide-border">{people.map((person) => <tr key={person.name}><td className="py-2.5 font-medium text-text-primary">{person.name}</td><td className="py-2.5 text-right text-text-secondary">{person.completed_books} / {person.available_books}</td><td className="py-2.5 text-right text-text-secondary">{person.completion_rate}%</td><td className="py-2.5 text-right text-text-secondary">{person.listened_hours}h</td></tr>)}</tbody></table><p className="sr-only">{title} ranking includes completed books, available library books, completion rate, and listening hours.</p></div>;
}

function AuthorNarratorAffinitySection({ data, isLoading, isError }: { data: AuthorNarratorAffinity | undefined; isLoading: boolean; isError: boolean }) {
  const [sortBy, setSortBy] = useState<AffinitySort>("completion_rate");
  if (isLoading) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Author & Narrator Affinity</h2><ChartSkeleton height={220} /></section>;
  if (isError) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Author & Narrator Affinity</h2><Card><CardContent><p className="text-sm text-destructive">Affinity rankings could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  const sortPeople = (people: AffinityPerson[]) => [...people].sort((left, right) => {
    const difference = right[sortBy] - left[sortBy];
    return difference || left.name.localeCompare(right.name);
  });
  const authors = sortPeople(data?.authors ?? []);
  const narrators = sortPeople(data?.narrators ?? []);
  return <section className="space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold text-text-primary">Author & Narrator Affinity</h2><p className="text-xs text-text-secondary mt-1">At least three library books are required. Multiple credits count for every listed person, so totals can exceed your book count.</p></div><div className="inline-flex rounded-lg border border-border p-1" role="group" aria-label="Affinity ranking sort"><button type="button" aria-pressed={sortBy === "completion_rate"} onClick={() => setSortBy("completion_rate")} className={`rounded-md px-3 py-1.5 text-sm ${sortBy === "completion_rate" ? "bg-accent text-white" : "text-text-secondary hover:bg-surface-hover"}`}>Completion rate</button><button type="button" aria-pressed={sortBy === "completed_books"} onClick={() => setSortBy("completed_books")} className={`rounded-md px-3 py-1.5 text-sm ${sortBy === "completed_books" ? "bg-accent text-white" : "text-text-secondary hover:bg-surface-hover"}`}>Completed</button><button type="button" aria-pressed={sortBy === "listened_hours"} onClick={() => setSortBy("listened_hours")} className={`rounded-md px-3 py-1.5 text-sm ${sortBy === "listened_hours" ? "bg-accent text-white" : "text-text-secondary hover:bg-surface-hover"}`}>Listening hours</button></div></div><div className="grid grid-cols-1 xl:grid-cols-2 gap-6"><Card><CardContent><h3 className="font-medium text-text-primary mb-3">Authors</h3><AffinityRanking title="Author" people={authors} /></CardContent></Card><Card><CardContent><h3 className="font-medium text-text-primary mb-3">Narrators</h3><AffinityRanking title="Narrator" people={narrators} /></CardContent></Card></div></section>;
}

function GenreCompletionCorrelationSection({ data, isLoading, isError }: { data: GenreCompletionCorrelation[] | undefined; isLoading: boolean; isError: boolean }) {
  if (isLoading) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Genre Completion Association</h2><ChartSkeleton height={220} /></section>;
  if (isError) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Genre Completion Association</h2><Card><CardContent><p className="text-sm text-destructive">Genre completion data could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  if (!data?.length) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Genre Completion Association</h2><Card><CardContent><p className="text-sm text-text-secondary">No genres have at least three started or completed books with known progress.</p></CardContent></Card></section>;
  return <section className="space-y-4"><div><h2 className="text-lg font-semibold text-text-primary">Genre Completion Association</h2><p className="text-xs text-text-secondary mt-1">This is an observed association in your library, not evidence that a genre causes a completion outcome.</p></div><Card><CardContent className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-left text-xs text-text-secondary"><tr><th className="pb-2 font-medium">Genre</th><th className="pb-2 font-medium text-right">Finished / known</th><th className="pb-2 font-medium text-right">Completion rate</th><th className="pb-2 font-medium text-right">Median pace</th></tr></thead><tbody className="divide-y divide-border">{data.map((genre) => <tr key={genre.name}><td className="py-2.5 font-medium text-text-primary">{genre.name}</td><td className="py-2.5 text-right text-text-secondary">{genre.completed_books} / {genre.known_progress_books}</td><td className="py-2.5 text-right text-text-secondary">{genre.completion_rate}%</td><td className="py-2.5 text-right text-text-secondary">{genre.median_days_to_finish == null ? "—" : `${genre.median_days_to_finish}d`}<span className="sr-only"> based on {genre.pace_qualifying_books} completed books with valid start and finish dates</span></td></tr>)}</tbody></table><p className="text-xs text-text-secondary mt-3">Completion rate uses only books with a known ABS progress record. Median pace excludes completed books without valid start and finish dates.</p></CardContent></Card></section>;
}

function DurationCompletionCorrelationSection({ data, isLoading, isError, onBookClick }: { data: DurationCompletionCorrelation | undefined; isLoading: boolean; isError: boolean; onBookClick: (bookId: string) => void }) {
  if (isLoading) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Length & Completion Pace</h2><ChartSkeleton height={300} /></section>;
  if (isError) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Length & Completion Pace</h2><Card><CardContent><p className="text-sm text-destructive">Length and completion pace could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  if (!data?.points.length) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Length & Completion Pace</h2><Card><CardContent><p className="text-sm text-text-secondary">No completed books with valid duration, start, and finish data are available for this period.</p></CardContent></Card></section>;
  const relationship = data.direction === "positive" ? "Longer books tend to take more days to finish in this sample." : data.direction === "negative" ? "Longer books tend to take fewer days to finish in this sample." : "There is no clear duration-and-pace relationship in this sample.";
  return <section className="space-y-4"><div><h2 className="text-lg font-semibold text-text-primary">Length & Completion Pace</h2><p className="text-xs text-text-secondary mt-1">Based on {data.qualifying_books} completed book{data.qualifying_books === 1 ? "" : "s"} with valid duration, start, and finish data.</p></div><Card><CardContent><ResponsiveContainer width="100%" height={300}><ScatterChart margin={{ top: 12, right: 12, bottom: 8, left: -8 }}><CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" /><XAxis type="number" dataKey="duration_hours" name="Length" unit="h" tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }} /><YAxis type="number" dataKey="days_to_finish" name="Days to finish" unit="d" tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }} /><Tooltip contentStyle={TOOLTIP_STYLE} cursor={CURSOR_STYLE} formatter={(value: number, name: string) => [name === "Length" ? `${value} hrs` : `${value} days`, name]} labelFormatter={(_, payload) => payload?.[0]?.payload?.title ?? "Completed book"} /><Scatter data={data.points} fill="var(--color-chart-3)" cursor="pointer" onClick={(point) => { const id = (point as { id?: string }).id; if (id) onBookClick(id); }} /></ScatterChart></ResponsiveContainer><p className="text-xs text-text-secondary mt-3">{data.qualifying_books >= 10 ? `${relationship}${data.correlation_coefficient == null ? " The Pearson coefficient is unavailable because the data lacks meaningful variation." : ` Pearson correlation: ${data.correlation_coefficient}.`}` : "A direction summary needs at least ten qualifying completed books."}</p><details className="mt-3 text-sm"><summary className="cursor-pointer text-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">Inspect completed titles</summary><div className="mt-2 flex flex-wrap gap-2">{data.points.map((point) => <button key={point.id} type="button" onClick={() => onBookClick(point.id)} className="rounded-md border border-border px-2 py-1 text-xs text-text-secondary hover:bg-surface-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">{point.title}</button>)}</div></details><p className="sr-only">Scatter plot of each completed book’s duration in hours against days to finish. Select a title to inspect the completed book.</p></CardContent></Card></section>;
}

export function ExtraListeningSection({ data, isLoading, isError, onBookClick }: { data: ExtraListening | undefined; isLoading: boolean; isError: boolean; onBookClick: (bookId: string) => void }) {
  if (isLoading) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Extra Listening</h2><ChartSkeleton height={160} /></section>;
  if (isError) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Extra Listening</h2><Card><CardContent><p className="text-sm text-destructive">Extra listening could not be loaded. Your other statistics are still available.</p></CardContent></Card></section>;
  if (!data || data.qualifying_books === 0) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Extra Listening</h2><Card><CardContent><p className="text-sm text-text-secondary">No completed books with valid media duration and listening data are available for this period.</p></CardContent></Card></section>;
  if (!data.books.length) return <section className="space-y-4"><h2 className="text-lg font-semibold text-text-primary">Extra Listening</h2><Card><CardContent><p className="text-sm text-text-secondary">No completed books reached 125% of their media duration in this period.</p></CardContent></Card></section>;
  return <section className="space-y-4"><div><h2 className="text-lg font-semibold text-text-primary">Extra Listening</h2><p className="text-xs text-text-secondary mt-1">Completed books with listening time at or above 125% of media duration.</p></div><Card><CardContent className="space-y-3">{data.books.map((book) => <button key={book.id} type="button" onClick={() => onBookClick(book.id)} className="flex w-full items-center justify-between gap-4 rounded-lg border border-border p-3 text-left hover:bg-surface-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"><span><span className="block font-medium text-text-primary">{book.title}</span><span className="block text-xs text-text-secondary mt-1">{book.author} · {book.listened_hours}h listened / {book.duration_hours}h media</span></span><span className="text-sm font-bold text-accent">{book.listening_ratio}%</span></button>)}<p className="text-xs text-text-secondary">This does not necessarily mean you re-listened: playback restarts, seeking, and ABS session accounting can also increase the ratio.</p></CardContent></Card></section>;
}

// ---------------------------------------------------------------------------
// Genre pie / donut chart
// ---------------------------------------------------------------------------

function genreData(genres: GenreCount[]): { name: string; books: number }[] {
  const sorted = [...genres].sort((a, b) => b.books - a.books);
  const top = sorted.slice(0, 8);
  const rest = sorted.slice(8);
  if (rest.length > 0) {
    top.push({ name: "Other", books: rest.reduce((s, g) => s + g.books, 0) });
  }
  return top;
}

function GenreChart({ data }: { data: GenreCount[] }) {
  const slices = genreData(data);
  if (!slices.length) return null;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={slices}
          dataKey="books"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={70}
          outerRadius={110}
          paddingAngle={2}
        >
          {slices.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => [v, "Books"]} />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Top list (authors / narrators)
// ---------------------------------------------------------------------------

function TopList({
  title,
  items,
  valueLabel = "books",
  linkPrefix,
}: {
  title: string;
  items: AuthorCount[];
  valueLabel?: string;
  linkPrefix: string;
}) {
  return (
    <div className="space-y-1">
      <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="text-sm text-text-secondary">No data</p>
      ) : (
        items.map((item, i) => (
          <div key={item.name} className="flex items-center gap-3 py-1.5">
            <span className="text-xs text-text-secondary w-4 text-right flex-shrink-0">
              {i + 1}
            </span>
            <Link
              to={`${linkPrefix}/${encodeURIComponent(item.name)}`}
              className="text-sm text-text-primary flex-1 truncate hover:text-accent hover:underline"
            >
              {item.name}
            </Link>
            <span className="text-sm font-medium text-text-secondary flex-shrink-0">
              {item.books} {valueLabel}
            </span>
          </div>
        ))
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Year in Recap
// ---------------------------------------------------------------------------

interface RecapCardProps {
  label: string;
  value: string | number;
  sub?: ReactNode;
}

function RecapCard({ label, value, sub, onClick }: RecapCardProps & { onClick?: () => void }) {
  const content = (
    <div className="bg-accent/10 border border-accent/20 rounded-xl p-5 flex flex-col gap-1">
      <p className="text-4xl font-bold text-accent">{value}</p>
      <p className="text-sm font-medium text-text-primary">{label}</p>
      {sub && <p className="text-xs text-text-secondary">{sub}</p>}
    </div>
  );
  return onClick ? (
    <button onClick={onClick} className="text-left rounded-xl hover:brightness-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
      {content}
    </button>
  ) : content;
}

function RecapSection({
  data,
  onBooksClick,
  onHoursClick,
}: {
  data: RecapStats;
  onBooksClick: () => void;
  onHoursClick: () => void;
}) {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-text-primary">Year in Recap</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <RecapCard label="Books finished" value={data.books_finished} onClick={onBooksClick} />
        <RecapCard
          label="Hours listened"
          value={Math.round(data.hours_listened)}
          sub={`${Math.round(data.hours_of_content)} hrs of content`}
          onClick={onHoursClick}
        />
        <RecapCard label="Active months" value={data.active_months} sub="out of 12" />
        {data.longest_book && (
          <RecapCard
            label="Longest book"
            value={formatDuration(data.longest_book.duration)}
            sub={<AbsBookLink itemId={data.longest_book.id} className="hover:text-accent hover:underline">{data.longest_book.title}</AbsBookLink>}
          />
        )}
        {data.shortest_book && (
          <RecapCard
            label="Shortest book"
            value={formatDuration(data.shortest_book.duration)}
            sub={<AbsBookLink itemId={data.shortest_book.id} className="hover:text-accent hover:underline">{data.shortest_book.title}</AbsBookLink>}
          />
        )}
        {data.fastest_read && (
          <RecapCard
            label="Fastest read (outlier)"
            value={`${data.fastest_read.days}d`}
            sub={<AbsBookLink itemId={data.fastest_read.id} className="hover:text-accent hover:underline">{data.fastest_read.title}</AbsBookLink>}
          />
        )}
        {data.slowest_read && (
          <RecapCard
            label="Slowest read (outlier)"
            value={`${data.slowest_read.days}d`}
            sub={<AbsBookLink itemId={data.slowest_read.id} className="hover:text-accent hover:underline">{data.slowest_read.title}</AbsBookLink>}
          />
        )}
        {data.top_series[0] && (
          <RecapCard
            label="Top series"
            value={data.top_series[0].books}
            sub={data.top_series[0].name}
          />
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Goal card
// ---------------------------------------------------------------------------

const RING_R = 54;
const RING_C = 2 * Math.PI * RING_R;

function GoalRing({ pct }: { pct: number }) {
  const dash = Math.min(pct, 1) * RING_C;
  return (
    <svg width="140" height="140" viewBox="0 0 140 140" className="flex-shrink-0">
      <circle cx="70" cy="70" r={RING_R} fill="none" stroke="var(--color-border)" strokeWidth="12" />
      <circle
        cx="70"
        cy="70"
        r={RING_R}
        fill="none"
        stroke="var(--color-chart-1)"
        strokeWidth="12"
        strokeDasharray={`${dash} ${RING_C}`}
        strokeLinecap="round"
        transform="rotate(-90 70 70)"
        style={{ transition: "stroke-dasharray 0.4s ease" }}
      />
    </svg>
  );
}

function paceLabel(booksFinished: number, target: number, year: string): string {
  const now = new Date();
  const y = Number(year);
  if (y !== now.getFullYear()) return "";
  const startOfYear = new Date(y, 0, 1).getTime();
  const endOfYear = new Date(y + 1, 0, 1).getTime();
  const elapsed = (now.getTime() - startOfYear) / (endOfYear - startOfYear);
  const expected = target * elapsed;
  if (booksFinished >= expected) return "On track";
  const behind = Math.ceil(expected - booksFinished);
  return `Behind by ${behind}`;
}

export function GoalForecastSummary({ data, isLoading, isError }: { data: GoalForecast | undefined; isLoading: boolean; isError: boolean }) {
  if (isLoading) return <Skeleton className="h-16 w-full mt-4" />;
  if (isError) return <p className="mt-4 pt-4 border-t border-border text-xs text-destructive">Goal forecast could not be loaded. Your goal progress is still available.</p>;
  if (!data?.has_goal) return null;
  if (!data.eligible) return data.ineligibility_reason ? <p className="mt-4 pt-4 border-t border-border text-xs text-text-secondary">Forecast unavailable: {data.ineligibility_reason}</p> : null;
  return <div className="mt-4 pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-2 gap-3"><div><p className="text-2xl font-bold text-text-primary">{data.projected_books}</p><p className="text-xs text-text-secondary">Estimated books by year end</p></div><div><p className="text-2xl font-bold text-text-primary">{data.required_books_per_week}</p><p className="text-xs text-text-secondary">Books per remaining week to reach your goal</p></div><p className="sm:col-span-2 text-xs text-text-secondary">Estimate based on {data.trailing_30_day_completions} completed book{data.trailing_30_day_completions === 1 ? "" : "s"} in the trailing 30 days.</p></div>;
}

function GoalCard({ booksFinished, year }: { booksFinished: number; year: string }) {
  const goals = useGoals();
  const setGoal = useSetGoal();
  const forecast = useGoalForecast(year);
  const [editing, setEditing] = useState(false);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const goal = goals.data?.find((g) => g.year === Number(year));
  const target = goal?.target_books ?? 0;
  const pct = target > 0 ? booksFinished / target : 0;
  const pace = target > 0 ? paceLabel(booksFinished, target, year) : "";

  function startEdit() {
    setInput(target > 0 ? String(target) : "");
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function cancelEdit() {
    setEditing(false);
  }

  function saveEdit() {
    const val = parseInt(input, 10);
    if (!val || val <= 0) { setEditing(false); return; }
    setGoal.mutate({ year: Number(year), target: val }, { onSuccess: () => setEditing(false) });
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") saveEdit();
    if (e.key === "Escape") cancelEdit();
  }

  if (goals.isLoading) return <Skeleton className="h-36 w-full rounded-xl" />;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">Reading Goal</h2>
        {!editing && (
          <button
            onClick={startEdit}
            className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors"
          >
            <Pencil className="w-3.5 h-3.5" />
            {target > 0 ? "Edit goal" : "Set goal"}
          </button>
        )}
      </div>

      <Card>
        <CardContent>
          {target === 0 && !editing ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
              <p className="text-sm text-text-secondary">No goal set for {year}.</p>
              <button
                onClick={startEdit}
                className="text-sm font-medium text-accent hover:underline"
              >
                Set a reading goal
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-6">
              <div className="relative flex-shrink-0">
                <GoalRing pct={pct} />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-text-primary leading-none">
                    {booksFinished}
                  </span>
                  <span className="text-xs text-text-secondary">of {target}</span>
                </div>
              </div>

              <div className="flex-1 space-y-2">
                <p className="text-text-primary font-medium">
                  {booksFinished >= target
                    ? "Goal reached!"
                    : `${target - booksFinished} book${target - booksFinished === 1 ? "" : "s"} to go`}
                </p>
                {pace && (
                  <span
                    className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${
                      pace === "On track"
                        ? "bg-green-500/10 text-green-500"
                        : "bg-amber-500/10 text-amber-500"
                    }`}
                  >
                    {pace}
                  </span>
                )}
                <div className="w-full bg-border rounded-full h-1.5 mt-2">
                  <div
                    className="bg-chart-1 h-1.5 rounded-full transition-all"
                    style={{ width: `${Math.min(pct * 100, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-text-secondary">
                  {Math.round(Math.min(pct, 1) * 100)}% complete
                </p>
              </div>
            </div>
          )}

          {target > 0 && <GoalForecastSummary data={forecast.data} isLoading={forecast.isLoading} isError={forecast.isError} />}

          {editing && (
            <div className="mt-4 pt-4 border-t border-border flex items-center gap-2">
              <label className="text-sm text-text-secondary flex-shrink-0">
                Target for {year}:
              </label>
              <input
                ref={inputRef}
                type="number"
                min={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                className="w-20 text-sm px-2 py-1 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                placeholder="24"
              />
              <span className="text-sm text-text-secondary">books</span>
              <button
                onClick={saveEdit}
                disabled={setGoal.isPending}
                className="ml-2 p-1 rounded-md text-green-500 hover:bg-green-500/10 transition-colors"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={cancelEdit}
                className="p-1 rounded-md text-text-secondary hover:bg-surface-hover transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Activity heatmap
// ---------------------------------------------------------------------------

const CELL = 11;
const GAP = 2;
const STEP = CELL + GAP;
const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function heatmapColor(minutes: number, max: number): string {
  if (minutes === 0 || max === 0) return "var(--color-border)";
  const ratio = minutes / max;
  if (ratio < 0.25) return "oklch(72% 0.17 160 / 30%)";
  if (ratio < 0.5) return "oklch(72% 0.17 160 / 55%)";
  if (ratio < 0.75) return "oklch(72% 0.17 160 / 80%)";
  return "var(--color-accent-positive)";
}

interface TooltipState {
  x: number;
  y: number;
  date: string;
  minutes: number;
}

function ActivityHeatmap({
  data,
  year,
  onDayClick,
}: {
  data: HeatmapPoint[];
  year: string;
  onDayClick?: (date: string) => void;
}) {
  const [tip, setTip] = useState<TooltipState | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const byDate = new Map<string, number>(data.map((p) => [p.date, p.minutes]));
  const max = data.reduce((m, p) => Math.max(m, p.minutes), 0);

  const jan1 = new Date(`${year}-01-01`);
  const startDow = jan1.getDay(); // 0=Sun
  const startOffset = startDow === 0 ? 6 : startDow - 1; // shift so Mon=0

  const totalDays = (Number(year) % 4 === 0 && (Number(year) % 100 !== 0 || Number(year) % 400 === 0)) ? 366 : 365;
  const totalCells = startOffset + totalDays;
  const cols = Math.ceil(totalCells / 7);

  const svgW = cols * STEP - GAP + 24; // +24 for day labels on left
  const svgH = 7 * STEP - GAP + 20;   // +20 for month labels on top

  const monthLabelX: { label: string; x: number }[] = [];
  for (let m = 0; m < 12; m++) {
    const firstDay = new Date(Number(year), m, 1);
    const dayIndex = Math.floor((firstDay.getTime() - jan1.getTime()) / 86400000);
    const col = Math.floor((startOffset + dayIndex) / 7);
    if (m < MONTHS.length) monthLabelX.push({ label: MONTHS[m] as string, x: 24 + col * STEP });
  }

  function onMouseEnter(e: React.MouseEvent<SVGRectElement>, date: string, minutes: number) {
    const svgRect = svgRef.current?.getBoundingClientRect();
    if (!svgRect) return;
    setTip({
      x: e.clientX - svgRect.left,
      y: e.clientY - svgRect.top,
      date,
      minutes,
    });
  }

  const cells: React.ReactNode[] = [];
  for (let i = 0; i < cols * 7; i++) {
    const dayIndex = i - startOffset;
    if (dayIndex < 0 || dayIndex >= totalDays) continue;
    const col = Math.floor(i / 7);
    const row = i % 7;
    const d = new Date(jan1.getTime() + dayIndex * 86400000);
    const dateStr = d.toISOString().slice(0, 10);
    const minutes = byDate.get(dateStr) ?? 0;
    cells.push(
      <rect
        key={dateStr}
        x={24 + col * STEP}
        y={20 + row * STEP}
        width={CELL}
        height={CELL}
        rx={2}
        fill={heatmapColor(minutes, max)}
        onMouseEnter={(e) => onMouseEnter(e, dateStr, minutes)}
        onMouseLeave={() => setTip(null)}
        onClick={() => minutes > 0 && onDayClick?.(dateStr)}
        style={{ cursor: minutes > 0 && onDayClick ? "pointer" : "default" }}
      />
    );
  }

  return (
    <div className="relative overflow-x-auto">
      <svg
        ref={svgRef}
        width={svgW}
        height={svgH}
        style={{ display: "block" }}
      >
        {/* Month labels */}
        {monthLabelX.map(({ label, x }) => (
          <text
            key={label}
            x={x}
            y={13}
            fontSize={10}
            fill="var(--color-text-secondary)"
            fontFamily="inherit"
          >
            {label}
          </text>
        ))}
        {/* Day labels */}
        {DAY_LABELS.map((label, row) => (
          label ? (
            <text
              key={row}
              x={0}
              y={20 + row * STEP + CELL - 1}
              fontSize={10}
              fill="var(--color-text-secondary)"
              fontFamily="inherit"
            >
              {label}
            </text>
          ) : null
        ))}
        {cells}
      </svg>

      {/* Tooltip */}
      {tip && (
        <div
          className="absolute pointer-events-none z-10 px-2 py-1 rounded-md text-xs whitespace-nowrap"
          style={{
            left: tip.x + 10,
            top: tip.y - 28,
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            color: "var(--color-text-primary)",
          }}
        >
          <span className="font-medium">{tip.date}</span>
          {" — "}
          {tip.minutes > 0 ? `${tip.minutes} min` : "No activity"}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-1.5 mt-2 justify-end">
        <span className="text-xs text-text-secondary">Less</span>
        {["var(--color-border)", "oklch(72% 0.17 160 / 30%)", "oklch(72% 0.17 160 / 55%)", "oklch(72% 0.17 160 / 80%)", "var(--color-accent-positive)"].map((c, i) => (
          <div key={i} className="w-3 h-3 rounded-sm" style={{ backgroundColor: c }} />
        ))}
        <span className="text-xs text-text-secondary">More</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Statistics drill-down
// ---------------------------------------------------------------------------

type DetailView = { kind: "books"; month?: string; durationBucket?: string; bookId?: string } | { kind: "hours"; month?: string } | { kind: "activity"; date?: string };

function formatFinishedAt(timestamp: number | null | undefined) {
  return timestamp ? new Date(timestamp).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "Finished date unavailable";
}

function isInDurationBucket(duration: number, bucket: string) {
  const hours = duration / 3600;
  if (bucket === "Under 5 hours") return hours < 5;
  if (bucket === "5–9:59 hours") return hours >= 5 && hours < 10;
  if (bucket === "10–19:59 hours") return hours >= 10 && hours < 20;
  if (bucket === "20–29:59 hours") return hours >= 20 && hours < 30;
  return bucket === "30 hours or more" && hours >= 30;
}

function StatisticsDetailDialog({
  open,
  onOpenChange,
  view,
  detail,
  isLoading,
  year,
  onSelectDay,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  view: DetailView;
  detail: StatisticsDetail | undefined;
  isLoading: boolean;
  year: string;
  onSelectDay: (date: string) => void;
}) {
  const period = view.kind === "books" || view.kind === "hours" ? view.month : undefined;
  const durationBucket = view.kind === "books" ? view.durationBucket : undefined;
  const bookId = view.kind === "books" ? view.bookId : undefined;
  const periodBooks = period
    ? (detail?.books ?? []).filter((book) => book.finished_at && new Date(book.finished_at).toISOString().startsWith(period))
    : detail?.books ?? [];
  const bucketBooks = durationBucket
    ? periodBooks.filter((book) => isInDurationBucket(book.duration, durationBucket))
    : periodBooks;
  const books = bookId ? bucketBooks.filter((book) => book.id === bookId) : bucketBooks;
  const listeningDays = period
    ? (detail?.listening_days ?? []).filter((day) => day.date.startsWith(period))
    : detail?.listening_days ?? [];
  const selectedDay = view.kind === "activity" && view.date
    ? detail?.listening_days.find((day) => day.date === view.date)
    : undefined;
  const title = view.kind === "books"
    ? bookId ? "Completed book" : durationBucket ? `Completed books: ${durationBucket}` : period ? `Books finished in ${period.length === 4 ? period : new Date(`${period}-01T12:00:00`).toLocaleDateString(undefined, { month: "long", year: "numeric" })}` : "Books finished"
    : view.kind === "hours" ? period ? `Listening time in ${new Date(`${period}-01T12:00:00`).toLocaleDateString(undefined, { month: "long", year: "numeric" })}` : "Listening time breakdown" : "Listening calendar";

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-2xl max-h-[85vh] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-xl border border-border bg-surface p-5 shadow-xl focus:outline-none">
          <div className="flex items-start justify-between gap-4 mb-5">
            <div>
              <Dialog.Title className="text-lg font-semibold text-text-primary">{title}</Dialog.Title>
              <p className="text-sm text-text-secondary mt-1">Click a coloured day to see the audiobooks behind it.</p>
            </div>
            <Dialog.Close asChild><button className="text-text-secondary hover:text-text-primary"><X className="w-5 h-5" /></button></Dialog.Close>
          </div>
          {isLoading ? <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}</div> : view.kind === "books" ? (
            <div className="space-y-2">
              {books.length === 0 ? <p className="py-8 text-center text-sm text-text-secondary">No books finished in this period.</p> : books.map((book) => (
                <div key={book.id} className="rounded-lg border border-border p-3">
                  <AbsBookLink itemId={book.id} className="block font-medium text-text-primary hover:text-accent hover:underline">{book.title}</AbsBookLink>
                  <p className="text-sm text-text-secondary">{book.author} · {formatFinishedAt(book.finished_at)}</p>
                </div>
              ))}
            </div>
          ) : view.kind === "hours" ? (
            <div className="space-y-3">
              {listeningDays.map((day) => (
                <div key={day.date} className="rounded-lg border border-border p-3 hover:bg-surface-hover">
                  <button onClick={() => onSelectDay(day.date)} className="w-full text-left">
                    <div className="flex justify-between gap-3"><span className="font-medium text-text-primary">{new Date(`${day.date}T12:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" })}</span><span className="text-sm text-accent">{day.minutes} min</span></div>
                  </button>
                  <p className="mt-1 text-sm text-text-secondary truncate">{day.books.map((book, index) => <span key={`${book.id}-${book.title}`}>{index > 0 && ", "}{book.id ? <AbsBookLink itemId={book.id} className="hover:text-accent hover:underline">{book.title}</AbsBookLink> : book.title}</span>)}</p>
                </div>
              ))}
              {listeningDays.length === 0 && <p className="py-8 text-center text-sm text-text-secondary">No listening sessions recorded.</p>}
            </div>
          ) : (
            <div className="space-y-5">
              {year !== "all" && <ActivityHeatmap data={(detail?.listening_days ?? []).map((day) => ({ date: day.date, minutes: day.minutes }))} year={year} onDayClick={onSelectDay} />}
              {selectedDay ? (
                <div className="rounded-lg border border-border p-4"><div className="flex items-center justify-between mb-3"><h3 className="font-medium text-text-primary">{selectedDay.date}</h3><span className="text-sm text-accent">{selectedDay.minutes} min</span></div><div className="space-y-2">{selectedDay.books.map((book) => <div key={`${book.id}-${book.title}`} className="flex justify-between gap-3 text-sm"><span className="text-text-primary">{book.id ? <AbsBookLink itemId={book.id} className="hover:text-accent hover:underline">{book.title}</AbsBookLink> : book.title}<span className="text-text-secondary"> · {book.author}</span></span><span className="text-text-secondary whitespace-nowrap">{book.minutes} min</span></div>)}</div></div>
              ) : <p className="text-sm text-text-secondary">Select an active day to see the audiobook and listening-time breakdown.</p>}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState({ year }: { year: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
      <BookOpen className="w-12 h-12 text-text-secondary opacity-30" />
      <p className="text-lg font-medium text-text-primary">
        {year === "all" ? "No books finished yet" : `No data for ${year}`}
      </p>
      <p className="text-sm text-text-secondary">
        {year === "all"
          ? "Finish some books and they'll show up here."
          : "Finish some books this year and they'll show up here."}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function StatisticsPage() {
  const [year, setYear] = useState(String(CURRENT_YEAR));
  const [detailView, setDetailView] = useState<DetailView>({ kind: "books" });
  const [detailOpen, setDetailOpen] = useState(false);

  const overall = useStatistics();
  const yearly = useYearlyStats(year);
  const recap = useRecap(year);
  const heatmap = useHeatmap(year);
  const habits = useListeningHabits(year);
  const completionVelocity = useCompletionVelocity(year);
  const monthlyComparison = useMonthlyComparison(year);
  const bookLengthPreferences = useBookLengthPreferences(year);
  const backlogHealth = useBacklogHealth();
  const seriesProgress = useSeriesProgress();
  const affinity = useAuthorNarratorAffinity();
  const genreCompletion = useGenreCompletionCorrelation();
  const durationCompletion = useDurationCompletionCorrelation(year);
  const extraListening = useExtraListening(year);
  const detail = useStatisticsDetail(year);

  const statsLoading = overall.isLoading || yearly.isLoading || (year !== "all" && (recap.isLoading || heatmap.isLoading));
  const hasData = !yearly.isLoading && (yearly.data?.books_in_year ?? 0) > 0;
  const noData = !yearly.isLoading && !hasData;

  const booksInYear = yearly.data?.books_in_year ?? 0;
  const totalHours = year === "all"
    ? (overall.data ? Math.round(overall.data.hours_listened) : 0)
    : Math.round(recap.data?.hours_listened ?? 0);
  const activeMonths = yearly.data?.monthly_chart.filter((month) => month.books > 0).length ?? 0;
  const avgPerMonth = year === "all"
    ? (overall.data ? overall.data.avg_books_per_month.toFixed(1) : "—")
    : activeMonths > 0 ? (booksInYear / activeMonths).toFixed(1) : "—";
  const longestStreak = year === "all"
    ? overall.data?.streak.longest ?? 0
    : longestConsecutiveDays(heatmap.data?.data ?? []);

  function openDetail(view: DetailView) {
    setDetailView(view);
    setDetailOpen(true);
  }

  function selectActivityDay(date: string) {
    setDetailView({ kind: "activity", date });
  }

  return (
    <div className="space-y-8 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-text-primary">Statistics</h1>
        <Select
          options={YEAR_OPTIONS}
          value={year}
          onValueChange={setYear}
          placeholder="Select year"
        />
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard
              label={year === "all" ? "All Books Finished" : `Books in ${year}`}
              value={booksInYear}
              icon={BookOpen}
              onClick={() => openDetail({ kind: "books" })}
            />
            <StatCard label={year === "all" ? "Total Hours" : `Hours in ${year}`} value={totalHours} icon={Clock} onClick={() => openDetail({ kind: "hours" })} />
            <StatCard label={year === "all" ? "Avg / Active Month" : `Avg / Active Month in ${year}`} value={avgPerMonth} icon={TrendingUp} />
            <StatCard label={year === "all" ? "Longest Streak" : `Longest Streak in ${year}`} value={`${longestStreak}d`} icon={Flame} onClick={() => openDetail({ kind: "activity" })} />
          </>
        )}
      </div>

      {/* Reading goal — not shown for all-time view */}
      {year !== "all" && <GoalCard booksFinished={booksInYear} year={year} />}

      <ListeningHabitsSection data={habits.data} isLoading={habits.isLoading} isError={habits.isError} />

      <CompletionVelocitySection data={completionVelocity.data} isLoading={completionVelocity.isLoading} isError={completionVelocity.isError} onMonthClick={(month) => openDetail({ kind: "books", month })} />

      <MonthlyComparisonSection data={monthlyComparison.data} isLoading={monthlyComparison.isLoading} isError={monthlyComparison.isError} onMonthClick={(month, metric) => openDetail(metric === "books" ? { kind: "books", month } : { kind: "hours", month })} />

      <BookLengthPreferencesSection data={bookLengthPreferences.data} isLoading={bookLengthPreferences.isLoading} isError={bookLengthPreferences.isError} onBucketClick={(durationBucket) => openDetail({ kind: "books", durationBucket })} />

      <BacklogHealthSection data={backlogHealth.data} isLoading={backlogHealth.isLoading} isError={backlogHealth.isError} />

      <SeriesProgressSection data={seriesProgress.data} isLoading={seriesProgress.isLoading} isError={seriesProgress.isError} />

      <AuthorNarratorAffinitySection data={affinity.data} isLoading={affinity.isLoading} isError={affinity.isError} />

      <GenreCompletionCorrelationSection data={genreCompletion.data} isLoading={genreCompletion.isLoading} isError={genreCompletion.isError} />

      <DurationCompletionCorrelationSection data={durationCompletion.data} isLoading={durationCompletion.isLoading} isError={durationCompletion.isError} onBookClick={(bookId) => openDetail({ kind: "books", bookId })} />

      <ExtraListeningSection data={extraListening.data} isLoading={extraListening.isLoading} isError={extraListening.isError} onBookClick={(bookId) => openDetail({ kind: "books", bookId })} />

      {/* Charts / lists / recap — or empty state */}
      {noData ? (
        <EmptyState year={year} />
      ) : (
        <>
          {/* Activity heatmap — year-specific only */}
          {year !== "all" && (
            <section className="space-y-4">
              <h2 className="text-lg font-semibold text-text-primary">Listening Activity</h2>
              <Card>
                <CardContent>
                  {heatmap.isLoading ? (
                    <ChartSkeleton height={120} />
                  ) : (
                    <ActivityHeatmap data={heatmap.data?.data ?? []} year={year} onDayClick={(date) => openDetail({ kind: "activity", date })} />
                  )}
                </CardContent>
              </Card>
            </section>
          )}

          {/* Genre + top lists */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Genre pie */}
            <section className="space-y-4">
              <h2 className="text-lg font-semibold text-text-primary">Genres</h2>
              <Card>
                <CardContent>
                  {yearly.isLoading ? (
                    <ChartSkeleton />
                  ) : (yearly.data?.genre_breakdown.length ?? 0) === 0 ? (
                    <p className="text-sm text-text-secondary text-center py-10">No genre data</p>
                  ) : (
                    <>
                      <GenreChart data={yearly.data?.genre_breakdown ?? []} />
                      {/* Legend */}
                      <div className="mt-4 grid grid-cols-2 gap-1">
                        {genreData(yearly.data?.genre_breakdown ?? []).map((g, i) => (
                          <div key={g.name} className="flex items-center gap-2 text-xs">
                            <span
                              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                              style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                            />
                            <span className="text-text-secondary truncate">{g.name}</span>
                            <span className="text-text-secondary ml-auto flex-shrink-0">
                              {g.books}
                            </span>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </section>

            {/* Authors + Narrators */}
            <div className="space-y-6">
              <section className="space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-text-primary">Top Authors</h2>
                  <Link
                    to="/authors?tab=library&sort=books"
                    className="text-xs text-text-secondary hover:text-accent transition-colors"
                  >
                    View all →
                  </Link>
                </div>
                <Card>
                  <CardContent>
                    {yearly.isLoading ? (
                      <div className="space-y-2">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Skeleton key={i} className="h-7 w-full" />
                        ))}
                      </div>
                    ) : (
                      <TopList
                        title=""
                        items={yearly.data?.top_authors ?? []}
                        linkPrefix="/authors"
                      />
                    )}
                  </CardContent>
                </Card>
              </section>

              <section className="space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-text-primary">Top Narrators</h2>
                  <Link
                    to="/narrators?sort=books"
                    className="text-xs text-text-secondary hover:text-accent transition-colors"
                  >
                    View all →
                  </Link>
                </div>
                <Card>
                  <CardContent>
                    {yearly.isLoading ? (
                      <div className="space-y-2">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Skeleton key={i} className="h-7 w-full" />
                        ))}
                      </div>
                    ) : (
                      <TopList
                        title=""
                        items={yearly.data?.top_narrators ?? []}
                        linkPrefix="/narrators"
                      />
                    )}
                  </CardContent>
                </Card>
              </section>
            </div>
          </div>

          {/* Year in Recap — year-specific only */}
          {year !== "all" && recap.data && <RecapSection data={recap.data} onBooksClick={() => openDetail({ kind: "books" })} onHoursClick={() => openDetail({ kind: "hours" })} />}
        </>
      )}
      <StatisticsDetailDialog
        open={detailOpen}
        onOpenChange={setDetailOpen}
        view={detailView}
        detail={detail.data}
        isLoading={detail.isLoading}
        year={year}
        onSelectDay={selectActivityDay}
      />
    </div>
  );
}
