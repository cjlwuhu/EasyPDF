import { describe, expect, it } from "vitest";

import { displayLanguageName, normalizePreferences, type UserPreferences } from "../src/preferences";

describe("user preferences", () => {
  it("normalizes invalid stored preferences to defaults", () => {
    expect(normalizePreferences({ language: "fr", theme: "midnight" })).toEqual({
      language: "zh",
      theme: "light"
    });
  });

  it("keeps valid language and theme values", () => {
    const preferences: UserPreferences = { language: "en", theme: "dark" };

    expect(normalizePreferences(preferences)).toEqual(preferences);
  });

  it("displays language names in Chinese", () => {
    expect(displayLanguageName("zh")).toBe("中文");
    expect(displayLanguageName("en")).toBe("English");
  });
}
);
