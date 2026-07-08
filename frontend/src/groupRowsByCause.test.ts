import { describe, expect, it } from "vitest";
import { groupRowsByCause } from "./hazopTableUtils";
import type { HazopRow } from "./data";

// Minimal HazopRow factory — only the fields groupRowsByCause reads (id, cause)
// matter; the rest are filled with valid-but-inert defaults.
function makeRow(overrides: Partial<HazopRow> & Pick<HazopRow, "id">): HazopRow {
  return {
    guideword: "Yok",
    deviation: "",
    cause: "",
    consequence: "",
    safeguard: "",
    severity: 1,
    likelihood: 1,
    risk: "Düşük",
    status: "Taslak",
    ...overrides,
  };
}

describe("groupRowsByCause", () => {
  it("groups rows that share a cause, preserving first-appearance order", () => {
    const rows = [
      makeRow({ id: 1, cause: "Valve fails open" }),
      makeRow({ id: 2, cause: "Strainer blockage" }),
      makeRow({ id: 3, cause: "Valve fails open" }),
    ];

    const groups = groupRowsByCause(rows);

    expect(groups).toHaveLength(2);
    // First-appearance order: "Valve fails open" seen before "Strainer blockage".
    expect(groups[0].key).toBe("cause:Valve fails open");
    expect(groups[0].rows.map((r) => r.id)).toEqual([1, 3]);
    expect(groups[1].key).toBe("cause:Strainer blockage");
    expect(groups[1].rows.map((r) => r.id)).toEqual([2]);
  });

  it("matches causes ignoring surrounding whitespace", () => {
    const rows = [
      makeRow({ id: 1, cause: "Same cause" }),
      makeRow({ id: 2, cause: "  Same cause  " }),
    ];

    const groups = groupRowsByCause(rows);

    expect(groups).toHaveLength(1);
    expect(groups[0].rows.map((r) => r.id)).toEqual([1, 2]);
  });

  it("gives each blank-cause row its own group keyed by row id", () => {
    const rows = [
      makeRow({ id: 1, cause: "" }),
      makeRow({ id: 2, cause: "   " }),
      makeRow({ id: 3, cause: "Real cause" }),
    ];

    const groups = groupRowsByCause(rows);

    expect(groups).toHaveLength(3);
    expect(groups[0].key).toBe("row:1");
    expect(groups[0].rows).toHaveLength(1);
    expect(groups[1].key).toBe("row:2");
    expect(groups[1].rows).toHaveLength(1);
    expect(groups[2].key).toBe("cause:Real cause");
  });

  it("returns an empty array for no rows", () => {
    expect(groupRowsByCause([])).toEqual([]);
  });
});
