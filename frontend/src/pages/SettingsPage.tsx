import { useEffect, useRef, useState } from "react";
import { Download, Upload } from "lucide-react";
import { Button, Input, Label, Select, Switch } from "@/components/ui";
import { useSettings, useUpdateSettings } from "@/hooks/useSettings";
import {
  downloadBackup,
  testAbsConnection,
  testLlmConnection,
  testNotifications,
  uploadRestore,
  type SettingsPatch,
  type SettingsRead,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-base font-semibold text-text-primary border-b border-border pb-2 mb-4">
      {children}
    </h2>
  );
}

function FieldRow({ label, htmlFor, children }: { label: string; htmlFor?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  );
}

function InlineFeedback({ text, isError }: { text: string; isError?: boolean }) {
  return (
    <p className={`text-xs mt-1 ${isError ? "text-red-500" : "text-green-600 dark:text-green-400"}`}>
      {text}
    </p>
  );
}

function useSavedFeedback() {
  const [saved, setSaved] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggerSaved = () => {
    setSaved(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setSaved(false), 3000);
  };

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  return { saved, triggerSaved };
}

// ---------------------------------------------------------------------------
// Section: Audiobookshelf Connection
// ---------------------------------------------------------------------------

function AbsSection({ settings }: { settings: SettingsRead }) {
  const update = useUpdateSettings();
  const { saved, triggerSaved } = useSavedFeedback();

  const [url, setUrl] = useState(settings.abs_url ?? "");
  const [token, setToken] = useState("");

  const [testStatus, setTestStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    if (!url) return;
    setTesting(true);
    setTestStatus(null);
    try {
      const res = await testAbsConnection({ url, token: token || null });
      if (res.ok) {
        const meta = res.metadata;
        const name = meta?.library_name as string | undefined;
        const count = meta?.book_count as number | undefined;
        const parts = ["Connected"];
        if (name) parts.push(name);
        if (count != null) parts.push(`${count} books`);
        setTestStatus({ ok: true, msg: parts.join(" · ") });
      } else {
        setTestStatus({ ok: false, msg: res.error ?? "Connection failed" });
      }
    } catch (e) {
      setTestStatus({ ok: false, msg: String(e) });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    const patch: SettingsPatch = { abs_url: url || null };
    if (token) patch.abs_token = token;
    update.mutate(patch, { onSuccess: triggerSaved });
  };

  return (
    <section className="space-y-4">
      <SectionHeading>Audiobookshelf Connection</SectionHeading>

      <FieldRow label="Base URL" htmlFor="abs-url">
        <Input
          id="abs-url"
          placeholder="http://192.168.1.110:13378"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          autoComplete="off"
        />
      </FieldRow>

      <FieldRow label="API Token" htmlFor="abs-token">
        <Input
          id="abs-token"
          type="password"
          placeholder={settings.abs_token === "" ? "••••••••  (set)" : "Paste token…"}
          value={token}
          onChange={(e) => setToken(e.target.value)}
          autoComplete="off"
        />
      </FieldRow>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={testing || !url}
          pendingText="Testing…"
        >
          Test Connection
        </Button>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={update.isPending}
          pendingText="Saving…"
        >
          Save
        </Button>
        {saved && <InlineFeedback text="Saved." />}
      </div>

      {testStatus && (
        <InlineFeedback text={testStatus.msg} isError={!testStatus.ok} />
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section: Notifications
// ---------------------------------------------------------------------------

function NotificationsSection({ settings }: { settings: SettingsRead }) {
  const update = useUpdateSettings();
  const { saved, triggerSaved } = useSavedFeedback();

  const [enabled, setEnabled] = useState(settings.notifications_enabled);
  const [appriseUrl, setAppriseUrl] = useState("");
  const [daysBefore, setDaysBefore] = useState(settings.notify_days_before);
  const [notifyTime, setNotifyTime] = useState(settings.notify_time);
  const [timezone, setTimezone] = useState(settings.timezone);

  const [testStatus, setTestStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    setTestStatus(null);
    try {
      const res = await testNotifications();
      setTestStatus({ ok: res.ok, msg: res.ok ? "Notification sent." : (res.error ?? "Delivery failed") });
    } catch (e) {
      setTestStatus({ ok: false, msg: String(e) });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    const patch: SettingsPatch = {
      notifications_enabled: enabled,
      notify_days_before: daysBefore,
      notify_time: notifyTime,
      timezone: timezone,
    };
    if (appriseUrl) patch.apprise_url = appriseUrl;
    update.mutate(patch, { onSuccess: triggerSaved });
  };

  return (
    <section className="space-y-4">
      <SectionHeading>Notifications</SectionHeading>

      <div className="flex items-center gap-3">
        <Switch id="notif-enabled" checked={enabled} onCheckedChange={setEnabled} />
        <Label htmlFor="notif-enabled" className="cursor-pointer">Enable notifications</Label>
      </div>

      <div className={`space-y-4 ${!enabled ? "opacity-50 pointer-events-none" : ""}`}>
        <FieldRow label="Apprise URL" htmlFor="apprise-url">
          <Input
            id="apprise-url"
            type="password"
            placeholder={settings.apprise_url === "" ? "••••••••  (set)" : "apprise://…"}
            value={appriseUrl}
            onChange={(e) => setAppriseUrl(e.target.value)}
            autoComplete="off"
            disabled={!enabled}
          />
        </FieldRow>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <FieldRow label="Days before release" htmlFor="days-before">
            <Input
              id="days-before"
              type="number"
              min={1}
              max={30}
              value={daysBefore}
              onChange={(e) => setDaysBefore(Number(e.target.value))}
              disabled={!enabled}
            />
          </FieldRow>

          <FieldRow label="Notify time" htmlFor="notify-time">
            <Input
              id="notify-time"
              type="time"
              value={notifyTime}
              onChange={(e) => setNotifyTime(e.target.value)}
              disabled={!enabled}
            />
          </FieldRow>

          <FieldRow label="Timezone" htmlFor="timezone">
            <Input
              id="timezone"
              placeholder="UTC"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              disabled={!enabled}
            />
          </FieldRow>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={testing || !settings.apprise_url}
          pendingText="Sending…"
        >
          Test Connection
        </Button>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={update.isPending}
          pendingText="Saving…"
        >
          Save
        </Button>
        {saved && <InlineFeedback text="Saved." />}
      </div>

      {testStatus && (
        <InlineFeedback text={testStatus.msg} isError={!testStatus.ok} />
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section: Release Tracker
// ---------------------------------------------------------------------------

function ReleaseTrackerSection({ settings }: { settings: SettingsRead }) {
  const update = useUpdateSettings();
  const { saved, triggerSaved } = useSavedFeedback();

  const [cron, setCron] = useState(settings.releases_refresh_cron);

  const handleSave = () => {
    update.mutate({ releases_refresh_cron: cron }, { onSuccess: triggerSaved });
  };

  return (
    <section className="space-y-4">
      <SectionHeading>Release Tracker</SectionHeading>

      <FieldRow label="Auto-refresh schedule (cron)" htmlFor="refresh-cron">
        <Input
          id="refresh-cron"
          placeholder="0 6 * * *"
          value={cron}
          onChange={(e) => setCron(e.target.value)}
        />
        <p className="text-xs text-text-secondary">
          Standard 5-field cron expression (minute hour day month weekday). Default: daily at 06:00 UTC.
        </p>
      </FieldRow>

      <div className="flex items-center gap-3">
        <Button
          size="sm"
          onClick={handleSave}
          disabled={update.isPending}
          pendingText="Saving…"
        >
          Save
        </Button>
        {saved && <InlineFeedback text="Saved." />}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section: Book Recommender
// ---------------------------------------------------------------------------

const VECTOR_BACKEND_OPTIONS = [
  { value: "python", label: "Pure Python" },
  { value: "faiss", label: "FAISS" },
];

function RecommenderSection({ settings }: { settings: SettingsRead }) {
  const update = useUpdateSettings();
  const { saved, triggerSaved } = useSavedFeedback();

  const [enabled, setEnabled] = useState(settings.recommender_enabled);
  const [backend, setBackend] = useState(settings.recommender_vector_backend);
  const [embedModel, setEmbedModel] = useState(settings.recommender_embed_model);
  const [topK, setTopK] = useState(settings.recommender_top_k);
  const [minSim, setMinSim] = useState(settings.recommender_min_similarity);
  const [explanations, setExplanations] = useState(settings.recommender_explanations_enabled);

  const handleSave = () => {
    update.mutate(
      {
        recommender_enabled: enabled,
        recommender_vector_backend: backend,
        recommender_embed_model: embedModel,
        recommender_top_k: topK,
        recommender_min_similarity: minSim,
        recommender_explanations_enabled: explanations,
      },
      { onSuccess: triggerSaved },
    );
  };

  return (
    <section className="space-y-4">
      <SectionHeading>Book Recommender</SectionHeading>

      <div className="flex items-center gap-3">
        <Switch id="rec-enabled" checked={enabled} onCheckedChange={setEnabled} />
        <Label htmlFor="rec-enabled" className="cursor-pointer">Enable recommender</Label>
      </div>

      <div className={`space-y-4 ${!enabled ? "opacity-50 pointer-events-none" : ""}`}>
        <FieldRow label="Vector backend" htmlFor="rec-backend">
          <Select
            options={VECTOR_BACKEND_OPTIONS}
            value={backend}
            onValueChange={setBackend}
          />
        </FieldRow>

        <FieldRow label="Embedding model" htmlFor="rec-embed">
          <Input
            id="rec-embed"
            placeholder="nomic-embed-text"
            value={embedModel}
            onChange={(e) => setEmbedModel(e.target.value)}
            disabled={!enabled}
          />
        </FieldRow>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldRow label="Top K results" htmlFor="rec-topk">
            <Input
              id="rec-topk"
              type="number"
              min={1}
              max={50}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              disabled={!enabled}
            />
          </FieldRow>

          <FieldRow label="Min similarity (0.0–1.0)" htmlFor="rec-minsim">
            <Input
              id="rec-minsim"
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={minSim}
              onChange={(e) => setMinSim(Number(e.target.value))}
              disabled={!enabled}
            />
          </FieldRow>
        </div>

        <div className="flex items-center gap-3">
          <Switch
            id="rec-explanations"
            checked={explanations}
            onCheckedChange={setExplanations}
            disabled={!enabled}
          />
          <Label htmlFor="rec-explanations" className={`cursor-pointer ${!enabled ? "opacity-50" : ""}`}>
            Generate explanations
          </Label>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button
          size="sm"
          onClick={handleSave}
          disabled={update.isPending}
          pendingText="Saving…"
        >
          Save
        </Button>
        {saved && <InlineFeedback text="Saved." />}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section: LLM / Ollama (6-step canonical flow)
// ---------------------------------------------------------------------------

const LLM_TYPE_OPTIONS = [
  { value: "ollama", label: "Ollama" },
  { value: "ollama_bearer", label: "Ollama with Bearer" },
  { value: "openai", label: "OpenAI-compatible" },
];

function LlmSection({ settings }: { settings: SettingsRead }) {
  const update = useUpdateSettings();
  const { saved, triggerSaved } = useSavedFeedback();

  const [llmType, setLlmType] = useState(settings.llm_type ?? "ollama");
  const [endpoint, setEndpoint] = useState(settings.llm_endpoint ?? "");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState(settings.llm_model ?? "");

  const [testStatus, setTestStatus] = useState<{ ok: boolean; msg: string; models?: string[] } | null>(null);
  const [testing, setTesting] = useState(false);

  const needsApiKey = llmType === "ollama_bearer" || llmType === "openai";

  const handleTest = async () => {
    if (!endpoint) return;
    setTesting(true);
    setTestStatus(null);
    try {
      const res = await testLlmConnection({
        endpoint,
        llm_type: llmType,
        api_key: needsApiKey && apiKey ? apiKey : null,
      });
      if (res.ok) {
        const modelList = res.models ?? [];
        setTestStatus({ ok: true, msg: `Connected — ${modelList.length} model(s) available`, models: modelList });
      } else {
        setTestStatus({ ok: false, msg: res.error ?? "Connection failed" });
      }
    } catch (e) {
      setTestStatus({ ok: false, msg: String(e) });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    const patch: SettingsPatch = {
      llm_type: llmType,
      llm_endpoint: endpoint || null,
      llm_model: model || null,
    };
    if (apiKey) patch.llm_api_key = apiKey;
    update.mutate(patch, { onSuccess: triggerSaved });
  };

  return (
    <section className="space-y-4">
      <SectionHeading>LLM / Ollama</SectionHeading>

      {/* Step 1 — type */}
      <FieldRow label="LLM type" htmlFor="llm-type">
        <Select
          options={LLM_TYPE_OPTIONS}
          value={llmType}
          onValueChange={setLlmType}
        />
      </FieldRow>

      {/* Step 2 — base URL */}
      <FieldRow label="Base URL" htmlFor="llm-endpoint">
        <Input
          id="llm-endpoint"
          placeholder="http://localhost:11434"
          value={endpoint}
          onChange={(e) => setEndpoint(e.target.value)}
          autoComplete="off"
        />
      </FieldRow>

      {/* Step 3 — API key (bearer/openai only) */}
      {needsApiKey && (
        <FieldRow label="API key" htmlFor="llm-apikey">
          <Input
            id="llm-apikey"
            type="password"
            placeholder={settings.llm_api_key === "" ? "••••••••  (set)" : "sk-…"}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            autoComplete="off"
          />
        </FieldRow>
      )}

      {/* Step 4 — test connection */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleTest}
        disabled={testing || !endpoint}
        pendingText="Testing…"
      >
        Test Connection
      </Button>

      {testStatus && (
        <InlineFeedback text={testStatus.msg} isError={!testStatus.ok} />
      )}

      {/* Step 5 — model chips */}
      {testStatus?.ok && testStatus.models && testStatus.models.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {testStatus.models.map((m) => (
            <button
              key={m}
              onClick={() => setModel(m)}
              className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                model === m
                  ? "bg-accent text-white border-accent"
                  : "bg-surface border-border text-text-secondary hover:border-accent hover:text-text-primary"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      )}

      {/* Step 6 — model input (editable) */}
      <FieldRow label="Selected model" htmlFor="llm-model">
        <Input
          id="llm-model"
          placeholder="llama3"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          autoComplete="off"
        />
      </FieldRow>

      <div className="flex items-center gap-3">
        <Button
          size="sm"
          onClick={handleSave}
          disabled={update.isPending}
          pendingText="Saving…"
        >
          Save
        </Button>
        {saved && <InlineFeedback text="Saved." />}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section: Backup & Restore
// ---------------------------------------------------------------------------

function BackupSection() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [restoreStatus, setRestoreStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleDownload = async () => {
    try {
      const blob = await downloadBackup();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `readingview_backup_${new Date().toISOString().slice(0, 10)}.tar.gz`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently ignore — browser already shows the error
    }
  };

  const handleRestore = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setRestoreStatus(null);
    try {
      await uploadRestore(file);
      setRestoreStatus({ ok: true, msg: "Restored successfully. Reload the page." });
    } catch (e) {
      setRestoreStatus({ ok: false, msg: String(e) });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <section className="space-y-4">
      <SectionHeading>Backup &amp; Restore</SectionHeading>

      <div className="flex flex-wrap gap-3 items-center">
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="w-4 h-4 mr-1.5" />
          Download Backup
        </Button>
      </div>

      <div className="space-y-2">
        <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">
          Warning: Restoring will replace all current data.
        </p>
        <div className="flex flex-wrap gap-3 items-center">
          <input
            ref={fileRef}
            type="file"
            accept=".tar.gz"
            className="text-sm text-text-secondary file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border file:border-border file:bg-surface file:text-xs file:text-text-primary file:cursor-pointer hover:file:bg-surface-hover"
          />
          <Button
            size="sm"
            onClick={handleRestore}
            disabled={uploading}
            pendingText="Restoring…"
          >
            <Upload className="w-4 h-4 mr-1.5" />
            Restore
          </Button>
        </div>
        {restoreStatus && (
          <InlineFeedback text={restoreStatus.msg} isError={!restoreStatus.ok} />
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const { data: settings, isLoading } = useSettings();

  if (isLoading || !settings) {
    return (
      <div className="p-6 text-sm text-text-secondary">Loading settings…</div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-10">
      <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
      <AbsSection settings={settings} />
      <NotificationsSection settings={settings} />
      <ReleaseTrackerSection settings={settings} />
      <RecommenderSection settings={settings} />
      <LlmSection settings={settings} />
      <BackupSection />
    </div>
  );
}
