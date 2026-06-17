import { describe, expect, it } from "vitest";

import { formatTranslationJobProgress } from "../src/utils/translationJob";

describe("translation job progress", () => {
  it("formats queued progress when no paragraphs are included", () => {
    expect(
      formatTranslationJobProgress({
        job_id: 1,
        document_id: 1,
        status: "queued",
        total_count: 0,
        completed_count: 0,
        failed_count: 0
      })
    ).toEqual({ label: "Queued", percent: 0 });
  });

  it("formats completed and failed counts as a percentage", () => {
    expect(
      formatTranslationJobProgress({
        job_id: 2,
        document_id: 1,
        status: "running",
        total_count: 4,
        completed_count: 2,
        failed_count: 1
      })
    ).toEqual({ label: "Running 3/4", percent: 75 });
  });
});
