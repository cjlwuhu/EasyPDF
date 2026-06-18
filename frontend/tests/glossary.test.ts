import { describe, expect, it } from "vitest";

import { describeGlossaryDeleteError, removeGlossaryTerm } from "../src/utils/glossary";

describe("glossary deletion", () => {
  it("removes only the deleted term", () => {
    const terms = [{ id: 1, label: "first" }, { id: 2, label: "second" }];

    expect(removeGlossaryTerm(terms, 1)).toEqual([{ id: 2, label: "second" }]);
  });

  it("explains backend connection failures", () => {
    expect(describeGlossaryDeleteError(new TypeError("Failed to fetch"))).toBe(
      "Backend is unavailable. Start EasyPDF and try again."
    );
  });

  it("preserves API error details", () => {
    expect(describeGlossaryDeleteError(new Error("Glossary term not found"))).toBe(
      "Glossary term not found"
    );
  });
});
