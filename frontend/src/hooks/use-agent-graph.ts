// Live "Super Agents" graph for the console. Mints a graph token, seeds from /snapshot, then
// follows the /events SSE stream (every frame is a full snapshot.replace). Returns the derived
// nodes + handoff edges the /agents page draws. All errors are surfaced, never thrown into render.

import { useEffect, useState } from "react";

import {
  type AgentGraph,
  type OpenOrcaSnapshot,
  deriveGraph,
  fetchGraphToken,
  fetchSnapshot,
  openAgentEvents,
} from "@/lib/openorca";

export interface AgentGraphState {
  graph: AgentGraph;
  connected: boolean;
  loading: boolean;
  error: string | null;
}

const EMPTY: AgentGraph = { nodes: [], edges: [], liveCalls: 0, empty: true };

export function useAgentGraph(): AgentGraphState {
  const [snapshot, setSnapshot] = useState<OpenOrcaSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let es: EventSource | null = null;

    (async () => {
      try {
        const token = await fetchGraphToken();
        if (cancelled) return;
        // Seed immediately so the page renders before the first SSE frame arrives.
        const seed = await fetchSnapshot(token);
        if (cancelled) return;
        setSnapshot(seed);
        setLoading(false);
        es = openAgentEvents(
          token,
          (snap) => {
            if (!cancelled) {
              setSnapshot(snap);
              setConnected(true);
            }
          },
          () => {
            if (!cancelled) setConnected(false);
          },
        );
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load agents");
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
      es?.close();
    };
  }, []);

  return {
    graph: snapshot ? deriveGraph(snapshot) : EMPTY,
    connected,
    loading,
    error,
  };
}
