import { describe, expect, it } from "vitest";

import {
  type OpenOrcaSnapshot,
  deriveGraph,
  specialistOf,
} from "./openorca";

function node(
  id: string,
  status: "active" | "idle",
  currentAction = "",
  collaboratingWith: string[] = [],
) {
  return {
    id,
    name: id.slice(id.lastIndexOf(":") + 1),
    status,
    currentAction,
    collaboratingWith,
  };
}

function snap(agents: OpenOrcaSnapshot["agents"]): OpenOrcaSnapshot {
  return {
    machines: [],
    agents,
    meta: { runtime: "realtyrecall", generatedAt: "t", connectionStatus: "connected" },
  };
}

describe("specialistOf", () => {
  it("extracts the specialist from a room:specialist id", () => {
    expect(specialistOf("t_org_1:concierge")).toBe("concierge");
    expect(specialistOf("t_org_1:property")).toBe("property");
    expect(specialistOf("t_org_1:scheduling")).toBe("scheduling");
  });

  it("returns null for an unknown specialist", () => {
    expect(specialistOf("t_org_1:mystery")).toBeNull();
    expect(specialistOf("garbage")).toBeNull();
  });
});

describe("deriveGraph", () => {
  it("is empty for a null snapshot (no live call)", () => {
    const g = deriveGraph(null);
    expect(g.empty).toBe(true);
    expect(g.nodes).toHaveLength(0);
    expect(g.edges).toHaveLength(0);
    expect(g.liveCalls).toBe(0);
  });

  it("is empty when a snapshot carries no agents", () => {
    expect(deriveGraph(snap([])).empty).toBe(true);
  });

  it("maps one active concierge and two idle specialists", () => {
    const g = deriveGraph(
      snap([
        node("r1:concierge", "active", "Greeting the caller"),
        node("r1:property", "idle"),
        node("r1:scheduling", "idle"),
      ]),
    );
    expect(g.empty).toBe(false);
    expect(g.liveCalls).toBe(1);
    expect(g.nodes).toHaveLength(3);
    const active = g.nodes.filter((n) => n.active);
    expect(active).toHaveLength(1);
    expect(active[0].specialist).toBe("concierge");
    expect(active[0].action).toBe("Greeting the caller");
  });

  it("dedupes a handoff into a single undirected edge", () => {
    // The backend lists the collaboration on both endpoints.
    const g = deriveGraph(
      snap([
        node("r1:concierge", "idle", "", ["r1:property"]),
        node("r1:property", "active", "Searching homes", ["r1:concierge"]),
        node("r1:scheduling", "idle"),
      ]),
    );
    expect(g.edges).toHaveLength(1);
    expect(g.edges[0]).toEqual({ a: "r1:concierge", b: "r1:property" });
  });

  it("drops nodes and edges that are not known specialists", () => {
    const g = deriveGraph(
      snap([
        node("r1:concierge", "active", "", ["r1:ghost"]),
        node("r1:ghost", "idle"),
      ]),
    );
    expect(g.nodes).toHaveLength(1);
    expect(g.nodes[0].specialist).toBe("concierge");
    expect(g.edges).toHaveLength(0);
  });

  it("counts distinct rooms as separate live calls", () => {
    const g = deriveGraph(
      snap([
        node("r1:concierge", "active"),
        node("r2:concierge", "active"),
      ]),
    );
    expect(g.liveCalls).toBe(2);
    expect(g.nodes).toHaveLength(2);
  });
});
