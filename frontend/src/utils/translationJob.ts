import type { TranslationJob } from "../types";

export interface TranslationJobProgress {
  label: string;
  percent: number;
}

export function formatTranslationJobProgress(job: TranslationJob): TranslationJobProgress {
  if (job.total_count <= 0) {
    return { label: titleCaseStatus(job.status), percent: 0 };
  }

  const finishedCount = job.completed_count + job.failed_count;
  const percent = Math.min(100, Math.round((finishedCount / job.total_count) * 100));
  return {
    label: `${titleCaseStatus(job.status)} ${finishedCount}/${job.total_count}`,
    percent
  };
}

function titleCaseStatus(status: string): string {
  return status
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
