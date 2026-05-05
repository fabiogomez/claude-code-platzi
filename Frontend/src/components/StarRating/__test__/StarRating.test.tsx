import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StarRating } from "../StarRating";

describe("StarRating Component", () => {
  it("renders full stars based on the average", () => {
    const { container } = render(<StarRating average={3} count={5} />);

    const fullStars = container.querySelectorAll('[class*="starFull"]');
    expect(fullStars.length).toBe(3);
  });

  it("renders 'No ratings (0)' when average is 0 and count is 0", () => {
    render(<StarRating average={0} count={0} />);

    expect(screen.getByText("No ratings (0)")).toBeDefined();
  });

  it("renders the average with one decimal", () => {
    render(<StarRating average={4.5} count={10} />);

    expect(screen.getByText("4.5 (10)")).toBeDefined();
  });

  it("renders with size sm without errors", () => {
    const { container } = render(<StarRating average={3.7} count={8} size="sm" />);

    expect(container.querySelector('[class*="sm"]')).not.toBeNull();
  });

  it("renders 5 stars total (full + half + empty = 5)", () => {
    const { container } = render(<StarRating average={3.5} count={12} />);

    const fullStars = container.querySelectorAll('[class*="starFull"]');
    const halfStars = container.querySelectorAll('[class*="starHalf"]');
    const emptyStars = container.querySelectorAll('[class*="starEmpty"]');

    expect(fullStars.length + halfStars.length + emptyStars.length).toBe(5);
  });

  it("renders a half star when average has >= 0.5 decimal", () => {
    const { container } = render(<StarRating average={2.5} count={4} />);

    const halfStars = container.querySelectorAll('[class*="starHalf"]');
    expect(halfStars.length).toBe(1);
  });

  it("does not render a half star when average has < 0.5 decimal", () => {
    const { container } = render(<StarRating average={3.2} count={7} />);

    const halfStars = container.querySelectorAll('[class*="starHalf"]');
    expect(halfStars.length).toBe(0);
  });
});
