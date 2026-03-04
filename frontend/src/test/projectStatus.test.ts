import { describe, it, expect } from "vitest";
import { getStatusInfo, PROJECT_STATUS_MAP } from "../types/projectStatus";

describe("getStatusInfo", () => {
  it("returns correct info for known statuses", () => {
    const info = getStatusInfo("new");
    expect(info.short).toBe("Nou");
    expect(info.color).toBe("gray");
  });

  it("returns BEP info for bep_generated", () => {
    const info = getStatusInfo("bep_generated");
    expect(info.short).toBe("BEP");
    expect(info.color).toBe("amber");
  });

  it("returns verified OK info", () => {
    const info = getStatusInfo("bep_verified_ok");
    expect(info.short).toBe("OK");
    expect(info.color).toBe("green");
  });

  it("falls back to 'new' for unknown status", () => {
    const info = getStatusInfo("unknown_status");
    expect(info).toEqual(PROJECT_STATUS_MAP.new);
  });

  it("has all expected statuses", () => {
    const expected = ["new", "context_defined", "bep_generated", "bep_verified_partial", "bep_verified_ok"];
    for (const s of expected) {
      expect(PROJECT_STATUS_MAP).toHaveProperty(s);
    }
  });
});
