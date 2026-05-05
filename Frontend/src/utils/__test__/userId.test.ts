import { describe, it, expect, beforeEach, vi } from "vitest";
import { getUserId } from "../userId";

describe("getUserId", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("generates and persists a UUID in localStorage", () => {
    const id = getUserId();

    expect(id).toBeTruthy();
    expect(id.length).toBeGreaterThan(0);
    expect(localStorage.getItem("platziflix_user_id")).toBe(id);
  });

  it("returns the same UUID on subsequent calls", () => {
    const firstId = getUserId();
    const secondId = getUserId();

    expect(firstId).toBe(secondId);
  });

  it("uses the key 'platziflix_user_id' in localStorage", () => {
    getUserId();

    expect(localStorage.getItem("platziflix_user_id")).not.toBeNull();
  });

  it("returns existing UUID from localStorage without generating a new one", () => {
    const existingId = "existing-uuid-1234";
    localStorage.setItem("platziflix_user_id", existingId);

    const id = getUserId();
    expect(id).toBe(existingId);
  });
});
