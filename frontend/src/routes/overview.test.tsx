// frontend/src/routes/overview.test.tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";

// Mock the API so the page renders without a backend.
vi.mock("@/lib/api", () => ({
  getAssistantPersona: () => Promise.resolve({}),
  getLiveListings: () => Promise.resolve([]),
  getPipeline: () => Promise.resolve({ bookings: [], calls: [] }),
  getBuyers: () => Promise.resolve([]),
}));
// Mock the memory chapter so the canvas-based graph never renders in jsdom.
vi.mock("@/components/app/memory-section", () => ({
  MemorySection: () => <div>memory-section</div>,
}));
vi.mock("@/components/app/match-card", () => ({ MatchCard: () => null }));
vi.mock("@/components/app/call-link-card", () => ({ CallLinkCard: () => null }));
vi.mock("@clerk/clerk-react", () => ({ useUser: () => ({ user: null }) }));

import Overview from "@/routes/overview";

beforeEach(() => vi.clearAllMocks());

test("Overview renders the three narrative sections", async () => {
  render(
    <MemoryRouter>
      <Overview />
    </MemoryRouter>,
  );
  expect(await screen.findByText(/always-on AI receptionist/i)).toBeInTheDocument();
  expect(screen.getByText("How it remembers")).toBeInTheDocument();
  expect(screen.getByText("memory-section")).toBeInTheDocument();
  expect(screen.getByText(/What your assistant has done/i)).toBeInTheDocument();
});
