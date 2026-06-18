import { afterEach, describe, expect, it, vi } from "vitest";

import { apiDownload } from "../src/api/client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiDownload", () => {
  it("returns the blob and UTF-8 response filename", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("docx-bytes", {
      status: 200,
      headers: {
        "Content-Disposition": "attachment; filename*=UTF-8''Paper_translated.docx"
      }
    })));

    const result = await apiDownload("/api/documents/1/translation.docx");

    expect(result.filename).toBe("Paper_translated.docx");
    expect(await result.blob.text()).toBe("docx-bytes");
  });

  it("throws the server response when download fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("No translations", { status: 409 })));

    await expect(apiDownload("/api/documents/1/translation.docx")).rejects.toThrow("No translations");
  });
});
