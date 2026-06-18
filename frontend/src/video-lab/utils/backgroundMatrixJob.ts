export interface BackgroundMatrixJob<TItem> {
  jobId: string;
  status: "pending" | "running" | "completed" | "failed";
  total: number;
  completed: number;
  items: TItem[];
  totalElapsedMs: number;
  error: string;
}

const POLL_INTERVAL_MS = 1000;

export async function runBackgroundMatrixJob<TItem>(
  apiBase: string,
  payload: unknown,
  onProgress: (job: BackgroundMatrixJob<TItem>) => void,
): Promise<BackgroundMatrixJob<TItem>> {
  const startResp = await fetch(`${apiBase}/style-family/background-matrix-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const started = await startResp.json();
  if (!startResp.ok) throw new Error(started.detail ?? `${startResp.status}`);

  while (true) {
    const resp = await fetch(
      `${apiBase}/style-family/background-matrix-jobs/${encodeURIComponent(started.jobId)}`,
    );
    const job = (await resp.json()) as BackgroundMatrixJob<TItem> & { detail?: string };
    if (!resp.ok) throw new Error(job.detail ?? `${resp.status}`);
    onProgress(job);
    if (job.status === "completed") return job;
    if (job.status === "failed") throw new Error(job.error || "背景矩阵渲染失败");
    await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));
  }
}
