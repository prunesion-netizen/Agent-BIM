import { describe, it, expect } from "vitest";
import { createDefaultProjectContext } from "../types/projectContext";

describe("createDefaultProjectContext", () => {
  it("creates a valid default context", () => {
    const ctx = createDefaultProjectContext();
    expect(ctx.project_name).toBe("");
    expect(ctx.project_code).toBe("");
    expect(ctx.project_type).toBe("building");
    expect(ctx.location_country).toBe("Romania");
    expect(ctx.client_type).toBe("public");
    expect(ctx.current_phase).toBe("PT");
    expect(ctx.bep_version).toBe("1.0");
    expect(ctx.cde_platform).toBe("acc");
    expect(ctx.main_exchange_format).toBe("ifc4_3");
  });

  it("has array for disciplines", () => {
    const ctx = createDefaultProjectContext();
    expect(Array.isArray(ctx.disciplines)).toBe(true);
  });

  it("has ISO standards enabled by default", () => {
    const ctx = createDefaultProjectContext();
    expect(ctx.iso_19650_1).toBe(true);
    expect(ctx.iso_19650_2).toBe(true);
  });

  it("has correct date format for bep_date", () => {
    const ctx = createDefaultProjectContext();
    expect(ctx.bep_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
