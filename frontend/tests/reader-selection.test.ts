import { describe, expect, it } from "vitest";

function shouldShowToolbar(selectedText: string): boolean {
  return selectedText.trim().length > 0;
}

describe("reader selection", () => {
  it("shows toolbar only when selected text is not empty", () => {
    expect(shouldShowToolbar("  ")).toBe(false);
    expect(shouldShowToolbar("translated paragraph")).toBe(true);
  });
});
