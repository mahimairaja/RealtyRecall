import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { mockHook } = vi.hoisted(() => ({ mockHook: vi.fn() }));
vi.mock("@/hooks/use-agent-graph", () => ({ useAgentGraph: mockHook }));

import Agents from "@/routes/agents";
import { deriveGraph, type OpenOrcaSnapshot } from "@/lib/openorca";

function state(graph: ReturnType<typeof deriveGraph>, extra = {}) {
  return { graph, connected: false, loading: false, error: null, ...extra };
}

beforeEach(() => vi.clearAllMocks());

describe("Super Agents page", () => {
  it("shows the three specialists and the empty state off a call", () => {
    mockHook.mockReturnValue(state(deriveGraph(null)));
    render(
      <MemoryRouter>
        <Agents />
      </MemoryRouter>,
    );
    expect(screen.getByText("Concierge")).toBeInTheDocument();
    expect(screen.getByText("Property")).toBeInTheDocument();
    expect(screen.getByText("Scheduling")).toBeInTheDocument();
    expect(screen.getByText("No active call")).toBeInTheDocument();
    expect(screen.getByText(/appear here during a live call/i)).toBeInTheDocument();
  });

  it("glows the active specialist and lights the handoff edge on a live call", () => {
    const snapshot: OpenOrcaSnapshot = {
      machines: [],
      agents: [
        {
          id: "r1:concierge",
          name: "Concierge",
          status: "idle",
          currentAction: "",
          collaboratingWith: ["r1:property"],
        },
        {
          id: "r1:property",
          name: "Property",
          status: "active",
          currentAction: "Searching homes near the marina",
          collaboratingWith: ["r1:concierge"],
        },
        {
          id: "r1:scheduling",
          name: "Scheduling",
          status: "idle",
          currentAction: "",
          collaboratingWith: [],
        },
      ],
      meta: { runtime: "realtyrecall", generatedAt: "t", connectionStatus: "connected" },
    };
    mockHook.mockReturnValue(state(deriveGraph(snapshot)));
    const { container } = render(
      <MemoryRouter>
        <Agents />
      </MemoryRouter>,
    );

    expect(screen.getByText("Live call in progress")).toBeInTheDocument();
    expect(screen.getByText("Searching homes near the marina")).toBeInTheDocument();

    const property = container.querySelector('[data-specialist="property"]');
    expect(property?.getAttribute("data-active")).toBe("true");
    const concierge = container.querySelector('[data-specialist="concierge"]');
    expect(concierge?.getAttribute("data-active")).toBe("false");

    const edge = container.querySelector('[data-edge="concierge-property"]');
    expect(edge?.getAttribute("data-active")).toBe("true");
    const idleEdge = container.querySelector('[data-edge="property-scheduling"]');
    expect(idleEdge?.getAttribute("data-active")).toBe("false");

    // No empty-state prompt while a call is live.
    expect(screen.queryByText(/appear here during a live call/i)).not.toBeInTheDocument();
  });
});
