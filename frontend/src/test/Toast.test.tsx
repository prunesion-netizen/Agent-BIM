import { describe, it, expect } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { ToastProvider, useToast } from "../components/Toast";

function TestComponent() {
  const toast = useToast();
  return (
    <div>
      <button onClick={() => toast.success("Success message!")}>Show Toast</button>
    </div>
  );
}

describe("Toast", () => {
  it("renders ToastProvider without error", () => {
    render(
      <ToastProvider>
        <div>child</div>
      </ToastProvider>
    );
    expect(screen.getByText("child")).toBeInTheDocument();
  });

  it("shows toast message on trigger", () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    act(() => {
      screen.getByText("Show Toast").click();
    });
    expect(screen.getByText("Success message!")).toBeInTheDocument();
  });
});
