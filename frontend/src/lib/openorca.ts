// Client for the backend OpenOrca live-agent contract (backend/src/api/endpoints/openorca.py).
// The console mints a short-lived graph token (Clerk-auth), then reads the tenant's live agent
// graph over /snapshot and the /events SSE stream. EventSource cannot send an Authorization
// header, so the token rides as a ?token= query param. Every SSE frame is a full snapshot.replace,
// so the reducer just takes the newest snapshot; deriveGraph turns it into nodes + handoff edges.

import { API_BASE, authHeaders } from "@/lib/api";

export const SPECIALISTS = ["concierge", "property", "scheduling"] as const;
export type Specialist = (typeof SPECIALISTS)[number];

export const SPECIALIST_LABEL: Record<Specialist, string> = {
  concierge: "Concierge",
  property: "Property",
  scheduling: "Scheduling",
};

export const SPECIALIST_BLURB: Record<Specialist, string> = {
  concierge: "Greets the caller and routes the conversation",
  property: "Searches listings and shows homes",
  scheduling: "Checks the calendar and books showings",
};

// Only the snapshot fields the console renders. The backend sends more per agent (unused here).
export interface AgentNode {
  id: string; // "<room>:<specialist>"
  name: string;
  status: "active" | "idle";
  currentAction: string;
  collaboratingWith: string[];
}

export interface OpenOrcaSnapshot {
  machines: { id: string; name: string; lastSeen: string }[];
  agents: AgentNode[];
  meta: { runtime: string; generatedAt: string; connectionStatus: string };
}

// A single node in the derived graph the UI draws.
export interface GraphNode {
  id: string;
  specialist: Specialist;
  label: string;
  active: boolean;
  action: string;
  room: string;
}

// An undirected handoff edge between two nodes (deduped).
export interface GraphEdge {
  a: string;
  b: string;
}

export interface AgentGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  liveCalls: number;
  empty: boolean;
}

/** The specialist half of a "<room>:<specialist>" node id, or null if it is not one of ours. */
export function specialistOf(nodeId: string): Specialist | null {
  const specialist = nodeId.slice(nodeId.lastIndexOf(":") + 1);
  return (SPECIALISTS as readonly string[]).includes(specialist)
    ? (specialist as Specialist)
    : null;
}

function roomOf(nodeId: string): string {
  return nodeId.slice(0, nodeId.lastIndexOf(":"));
}

/**
 * Pure reducer: turn a snapshot into the nodes + deduped handoff edges the UI draws.
 * Nodes keep the backend order (concierge, property, scheduling per call). Edges are made
 * undirected and deduped, since the backend lists each collaboration on both endpoints.
 */
export function deriveGraph(snapshot: OpenOrcaSnapshot | null): AgentGraph {
  const agents = snapshot?.agents ?? [];
  const nodes: GraphNode[] = [];
  for (const a of agents) {
    const specialist = specialistOf(a.id);
    if (!specialist) continue;
    nodes.push({
      id: a.id,
      specialist,
      label: a.name || SPECIALIST_LABEL[specialist],
      active: a.status === "active",
      action: a.currentAction ?? "",
      room: roomOf(a.id),
    });
  }
  const known = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: GraphEdge[] = [];
  for (const a of agents) {
    for (const other of a.collaboratingWith ?? []) {
      if (!known.has(a.id) || !known.has(other)) continue;
      const [x, y] = a.id < other ? [a.id, other] : [other, a.id];
      const key = `${x}|${y}`;
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push({ a: x, b: y });
    }
  }
  const rooms = new Set(nodes.map((n) => n.room));
  return { nodes, edges, liveCalls: rooms.size, empty: nodes.length === 0 };
}

/** Mint a short-lived graph token scoped to the signed-in realtor's tenant. */
export async function fetchGraphToken(): Promise<string> {
  const res = await fetch(`${API_BASE}/openorca/graph-token`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`graph-token failed: ${res.status}`);
  const body = (await res.json()) as { token: string };
  return body.token;
}

/** One-shot read of the current live-agent snapshot. */
export async function fetchSnapshot(token: string): Promise<OpenOrcaSnapshot> {
  const res = await fetch(
    `${API_BASE}/openorca/snapshot?token=${encodeURIComponent(token)}`,
  );
  if (!res.ok) throw new Error(`snapshot failed: ${res.status}`);
  return (await res.json()) as OpenOrcaSnapshot;
}

/**
 * Subscribe to the live event stream. Every frame is a snapshot.replace, so onSnapshot fires
 * with the newest snapshot each time. Returns the EventSource so the caller can close it.
 */
export function openAgentEvents(
  token: string,
  onSnapshot: (snapshot: OpenOrcaSnapshot) => void,
  onError?: () => void,
): EventSource {
  const es = new EventSource(
    `${API_BASE}/openorca/events?token=${encodeURIComponent(token)}`,
  );
  es.onmessage = (ev) => {
    try {
      const frame = JSON.parse(ev.data) as {
        type: string;
        snapshot?: OpenOrcaSnapshot;
      };
      if (frame.type === "snapshot.replace" && frame.snapshot) {
        onSnapshot(frame.snapshot);
      }
    } catch {
      // A malformed frame (or a keep-alive comment) is ignored; the next frame is a full replace.
    }
  };
  if (onError) es.onerror = () => onError();
  return es;
}
