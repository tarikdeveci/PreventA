import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { HazopTable } from "./App";
import type { HazopRow } from "./data";

function makeRow(overrides: Partial<HazopRow> & Pick<HazopRow, "id">): HazopRow {
  return {
    guideword: "Yok",
    deviation: "No flow",
    cause: "Shared cause",
    consequence: "",
    safeguard: "",
    severity: 2,
    likelihood: 2,
    risk: "Orta",
    status: "Taslak",
    ...overrides,
  };
}

function renderTable(
  rows: HazopRow[],
  options: Partial<{
    selectedRow: number;
    readOnly: boolean;
    hiddenColumns: Set<string>;
    onSelectRow: (id: number) => void;
    onUpdateRow: (id: number, field: keyof HazopRow, value: string) => void;
    onAddConsequence: (fromRow: HazopRow) => void;
  }> = {},
) {
  const props = {
    selectedRow: options.selectedRow ?? rows[0]?.id ?? 0,
    onSelectRow: options.onSelectRow ?? vi.fn(),
    onUpdateRow: options.onUpdateRow ?? vi.fn(),
    onAddConsequence: options.onAddConsequence ?? vi.fn(),
    readOnly: options.readOnly ?? false,
    hiddenColumns: options.hiddenColumns ?? new Set<string>(),
  };

  const result = render(<HazopTable rows={rows} {...props} />);
  return { ...result, props };
}

describe("HazopTable", () => {
  it("renders one cause cell spanning all consequences for the same cause", () => {
    const rows = [
      makeRow({ id: 1, consequence: "Loss of feed" }),
      makeRow({ id: 2, consequence: "Pump damage" }),
      makeRow({ id: 3, cause: "Independent cause", consequence: "High pressure" }),
    ];

    const { container } = renderTable(rows);

    const causeCells = container.querySelectorAll("td.cause-cell");
    expect(causeCells).toHaveLength(2);
    expect(causeCells[0]).toHaveAttribute("rowspan", "2");
    expect(causeCells[1]).toHaveAttribute("rowspan", "1");
    expect(screen.getAllByRole("button", { name: /consequence/i })).toHaveLength(2);
  });

  it("updates every row in a cause group when the grouped cause is edited", async () => {
    const onUpdateRow = vi.fn();
    const rows = [
      makeRow({ id: 1, cause: "Shared cause" }),
      makeRow({ id: 2, cause: "Shared cause" }),
    ];

    renderTable(rows, { onUpdateRow });

    fireEvent.change(screen.getByLabelText("1. cause"), { target: { value: "New cause" } });

    expect(onUpdateRow).toHaveBeenCalledWith(1, "cause", "New cause");
    expect(onUpdateRow).toHaveBeenCalledWith(2, "cause", "New cause");
  });

  it("adds a consequence from the grouped cause button without selecting the row", async () => {
    const user = userEvent.setup();
    const onAddConsequence = vi.fn();
    const onSelectRow = vi.fn();
    const rows = [
      makeRow({ id: 1, cause: "Shared cause" }),
      makeRow({ id: 2, cause: "Shared cause" }),
    ];

    renderTable(rows, { onAddConsequence, onSelectRow });

    await user.click(screen.getByRole("button", { name: /consequence/i }));

    expect(onAddConsequence).toHaveBeenCalledWith(rows[0]);
    expect(onSelectRow).not.toHaveBeenCalled();
  });

  it("renders flat rows when the cause column is hidden", () => {
    const rows = [
      makeRow({ id: 1, cause: "Shared cause" }),
      makeRow({ id: 2, cause: "Shared cause" }),
    ];

    const { container } = renderTable(rows, { hiddenColumns: new Set(["cause"]) });

    expect(container.querySelector("td.cause-cell")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /consequence/i })).not.toBeInTheDocument();
    expect(within(screen.getByRole("table")).getAllByRole("row")).toHaveLength(3);
  });
});
