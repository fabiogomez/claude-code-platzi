import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RatingForm } from "../RatingForm";

// Mock crypto.randomUUID
Object.defineProperty(globalThis, "crypto", {
  value: {
    randomUUID: () => "test-uuid-1234-5678-9012",
  },
});

describe("RatingForm Component", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders the title 'Rate this course'", () => {
    render(<RatingForm courseSlug="test-course" />);

    expect(screen.getByText("Rate this course")).toBeDefined();
  });

  it("renders 5 star buttons", () => {
    render(<RatingForm courseSlug="test-course" />);

    const starButtons = screen.getAllByRole("button", { name: /Rate \d out of 5 stars/ });
    expect(starButtons.length).toBe(5);
  });

  it("submit button is initially disabled", () => {
    render(<RatingForm courseSlug="test-course" />);

    const submitButton = screen.getByText("Submit Rating");
    expect(submitButton).toBeDisabled();
  });

  it("clicking a star selects the score and enables submit", () => {
    render(<RatingForm courseSlug="test-course" />);

    const starButtons = screen.getAllByRole("button", { name: /Rate \d out of 5 stars/ });
    fireEvent.click(starButtons[3]); // Click 4th star

    expect(screen.getByText("4/5")).toBeDefined();
    expect(screen.getByText("Submit Rating")).not.toBeDisabled();
  });

  it("renders the comment textarea", () => {
    render(<RatingForm courseSlug="test-course" />);

    const textarea = screen.getByPlaceholderText("Leave an optional comment...");
    expect(textarea).toBeDefined();
  });

  it("on successful submit, shows a success message", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, score: 5 }),
    });

    render(<RatingForm courseSlug="test-course" />);

    const starButtons = screen.getAllByRole("button", { name: /Rate \d out of 5 stars/ });
    fireEvent.click(starButtons[4]); // Click 5th star

    const submitButton = screen.getByText("Submit Rating");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Rating submitted successfully")).toBeDefined();
    });
  });

  it("on submit with network error, shows an error message", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    render(<RatingForm courseSlug="test-course" />);

    const starButtons = screen.getAllByRole("button", { name: /Rate \d out of 5 stars/ });
    fireEvent.click(starButtons[2]); // Click 3rd star

    const submitButton = screen.getByText("Submit Rating");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Error submitting rating. Please try again.")).toBeDefined();
    });
  });
});
