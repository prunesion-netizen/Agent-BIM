import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatusBadge from "../components/StatusBadge";

describe("StatusBadge", () => {
  it("renders with correct label for 'new' status", () => {
    render(<StatusBadge status="new" />);
    expect(screen.getByText("Nou")).toBeInTheDocument();
  });

  it("renders with correct label for 'bep_generated'", () => {
    render(<StatusBadge status="bep_generated" />);
    expect(screen.getByText("BEP")).toBeInTheDocument();
  });

  it("renders with correct label for 'bep_verified_ok'", () => {
    render(<StatusBadge status="bep_verified_ok" />);
    expect(screen.getByText("OK")).toBeInTheDocument();
  });

  it("hides label when showLabel=false", () => {
    render(<StatusBadge status="new" showLabel={false} />);
    expect(screen.queryByText("Nou")).not.toBeInTheDocument();
  });

  it("falls back gracefully for unknown status", () => {
    render(<StatusBadge status="unknown_xyz" />);
    expect(screen.getByText("Nou")).toBeInTheDocument();
  });
});
