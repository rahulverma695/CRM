import { setActivePinia, createPinia } from "pinia";
import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "./auth";

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it("starts unauthenticated", () => {
    const auth = useAuthStore();
    expect(auth.isAuthenticated).toBe(false);
  });

  it("setTokens marks authenticated and persists", () => {
    const auth = useAuthStore();
    auth.setTokens({ access_token: "a", refresh_token: "r" });
    expect(auth.isAuthenticated).toBe(true);
    expect(localStorage.getItem("access_token")).toBe("a");
  });

  it("logout clears state and storage", () => {
    const auth = useAuthStore();
    auth.setTokens({ access_token: "a", refresh_token: "r" });
    auth.logout();
    expect(auth.isAuthenticated).toBe(false);
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});
