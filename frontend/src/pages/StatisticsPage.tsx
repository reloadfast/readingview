import { useRef, useState } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { BookOpen, Clock, TrendingUp, Flame, Pencil, Check, X } from "lucide-react";
import { Card, CardContent, Skeleton, Select } from "@/components/ui";
import { useStatistics, useYearlyStats, useRecap, useHeatmap } from "@/hooks/useStatistics";
import { useGoals, useSetGoal } from "@/hooks/useGoals";
import { formatDuration } from "@/lib/utils";
import type { RecapStats, AuthorCount, GenreCount, HeatmapPoint } from "@/lib/api";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CURRENT_YEAR = new Date().getFullYear();

const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => {
  const y = String(CURRENT_YEAR - i);
  return { value: y, label: y };
});

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
// Stat card
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
}) {
  return (
    <Card>
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
}

// ---------------------------------------------------------------------------
// Monthly bar chart
// ---------------------------------------------------------------------------

function MonthlyChart({ data }: { data: { month: string; books: number }[] }) {
  if (!data.length) return null;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--color-border)"
          vertical={false}
        />
        <XAxis
          dataKey="month"
          tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          cursor={CURSOR_STYLE}
          formatter={(v: number) => [v, "Books"]}
        />
        <Bar dataKey="books" fill="var(--color-chart-1)" radius={[4, 4, 0, 0]} maxBarSize={40} />
      </BarChart>
    </ResponsiveContainer>
  );
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
}: {
  title: string;
  items: AuthorCount[];
  valueLabel?: string;
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
            <span className="text-sm text-text-primary flex-1 truncate">{item.name}</span>
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
  sub?: string;
}

function RecapCard({ label, value, sub }: RecapCardProps) {
  return (
    <div className="bg-accent/10 border border-accent/20 rounded-xl p-5 flex flex-col gap-1">
      <p className="text-4xl font-bold text-accent">{value}</p>
      <p className="text-sm font-medium text-text-primary">{label}</p>
      {sub && <p className="text-xs text-text-secondary">{sub}</p>}
    </div>
  );
}

function RecapSection({ data }: { data: RecapStats }) {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-text-primary">Year in Recap</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <RecapCard label="Books finished" value={data.books_finished} />
        <RecapCard
          label="Hours listened"
          value={Math.round(data.hours_listened)}
          sub={`${Math.round(data.hours_of_content)} hrs of content`}
        />
        <RecapCard label="Active months" value={data.active_months} sub="out of 12" />
        {data.longest_book && (
          <RecapCard
            label="Longest book"
            value={formatDuration(data.longest_book.duration)}
            sub={data.longest_book.title}
          />
        )}
        {data.shortest_book && (
          <RecapCard
            label="Shortest book"
            value={formatDuration(data.shortest_book.duration)}
            sub={data.shortest_book.title}
          />
        )}
        {data.fastest_read && (
          <RecapCard
            label="Fastest read"
            value={`${data.fastest_read.days}d`}
            sub={data.fastest_read.title}
          />
        )}
        {data.slowest_read && (
          <RecapCard
            label="Slowest read"
            value={`${data.slowest_read.days}d`}
            sub={data.slowest_read.title}
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

function GoalCard({ booksFinished, year }: { booksFinished: number; year: string }) {
  const goals = useGoals();
  const setGoal = useSetGoal();
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

function ActivityHeatmap({ data, year }: { data: HeatmapPoint[]; year: string }) {
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
    monthLabelX.push({ label: MONTHS[m]!, x: 24 + col * STEP });
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
        style={{ cursor: minutes > 0 ? "pointer" : "default" }}
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
// Empty state
// ---------------------------------------------------------------------------

function EmptyState({ year }: { year: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
      <BookOpen className="w-12 h-12 text-text-secondary opacity-30" />
      <p className="text-lg font-medium text-text-primary">No data for {year}</p>
      <p className="text-sm text-text-secondary">
        Finish some books this year and they'll show up here.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function StatisticsPage() {
  const [year, setYear] = useState(String(CURRENT_YEAR));

  const overall = useStatistics();
  const yearly = useYearlyStats(year);
  const recap = useRecap(year);
  const heatmap = useHeatmap(year);

  const statsLoading = overall.isLoading || yearly.isLoading;
  const hasData = !yearly.isLoading && (yearly.data?.books_in_year ?? 0) > 0;
  const noData = !yearly.isLoading && !hasData;

  const booksInYear = yearly.data?.books_in_year ?? 0;
  const totalHours = overall.data ? Math.round(overall.data.hours_listened) : 0;
  const avgPerMonth = overall.data
    ? overall.data.avg_books_per_month.toFixed(1)
    : "—";
  const longestStreak = overall.data?.streak.longest ?? 0;

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
            <StatCard label={`Books in ${year}`} value={booksInYear} icon={BookOpen} />
            <StatCard label="Total Hours" value={totalHours} icon={Clock} />
            <StatCard label="Avg / Month" value={avgPerMonth} icon={TrendingUp} />
            <StatCard label="Longest Streak" value={`${longestStreak}d`} icon={Flame} />
          </>
        )}
      </div>

      {/* Reading goal */}
      <GoalCard booksFinished={booksInYear} year={year} />

      {/* Charts / lists / recap — or empty state */}
      {noData ? (
        <EmptyState year={year} />
      ) : (
        <>
          {/* Activity heatmap */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-text-primary">Listening Activity</h2>
            <Card>
              <CardContent>
                {heatmap.isLoading ? (
                  <ChartSkeleton height={120} />
                ) : (
                  <ActivityHeatmap data={heatmap.data?.data ?? []} year={year} />
                )}
              </CardContent>
            </Card>
          </section>

          {/* Monthly breakdown */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-text-primary">Monthly Breakdown</h2>
            <Card>
              <CardContent>
                {yearly.isLoading ? (
                  <ChartSkeleton />
                ) : (
                  <MonthlyChart data={yearly.data?.monthly_chart ?? []} />
                )}
              </CardContent>
            </Card>
          </section>

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
                <h2 className="text-lg font-semibold text-text-primary">Top Authors</h2>
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
                      />
                    )}
                  </CardContent>
                </Card>
              </section>

              <section className="space-y-3">
                <h2 className="text-lg font-semibold text-text-primary">Top Narrators</h2>
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
                      />
                    )}
                  </CardContent>
                </Card>
              </section>
            </div>
          </div>

          {/* Year in Recap */}
          {recap.data && <RecapSection data={recap.data} />}
        </>
      )}
    </div>
  );
}
