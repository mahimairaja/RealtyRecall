// The "Super Agents" console page. One caller is handled by three specialists that hand off
// within a single call: a Concierge routes, a Property agent searches and shows homes, and a
// Scheduling agent books. This page shows that roster live from the backend /openorca graph:
// the active specialist glows with its current action, and handoffs light up as edges. Off a
// call the roster still renders (idle), so a realtor always sees who answers their phone.
import { Sparkles } from "lucide-react";

import { useAgentGraph } from "@/hooks/use-agent-graph";
import {
  SPECIALISTS,
  SPECIALIST_BLURB,
  SPECIALIST_LABEL,
  type AgentGraph,
  type Specialist,
} from "@/lib/openorca";
import { pickByAgentId } from "@/lib/agent-avatars";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// Fixed stage positions (percent) so the SVG edge layer and the node cards share one coordinate
// space and stay aligned as the stage resizes. A shallow arc: Concierge left, Property up-center,
// Scheduling right.
const POS: Record<Specialist, { x: number; y: number }> = {
  concierge: { x: 16, y: 58 },
  property: { x: 50, y: 20 },
  scheduling: { x: 84, y: 58 },
};

// The three possible handoff pairs, drawn as faint baseline connectors (topology) and lit when
// an actual handoff is happening this call.
const PAIRS: [Specialist, Specialist][] = [
  ["concierge", "property"],
  ["property", "scheduling"],
  ["concierge", "scheduling"],
];

interface RosterEntry {
  specialist: Specialist;
  active: boolean;
  action: string;
}

// Collapse the live graph (which is keyed per call) onto the fixed three-role roster: a role is
// active if any live call has it active, and an edge is lit if any call has that handoff.
function roster(graph: AgentGraph): {
  entries: RosterEntry[];
  activeEdges: Set<string>;
} {
  const entries = SPECIALISTS.map((specialist) => {
    const live = graph.nodes.find((n) => n.specialist === specialist && n.active);
    return { specialist, active: Boolean(live), action: live?.action ?? "" };
  });
  const spec = new Map(graph.nodes.map((n) => [n.id, n.specialist]));
  const activeEdges = new Set<string>();
  for (const e of graph.edges) {
    const a = spec.get(e.a);
    const b = spec.get(e.b);
    if (a && b && a !== b) activeEdges.add([a, b].sort().join("-"));
  }
  return { entries, activeEdges };
}

function edgeKey(a: Specialist, b: Specialist): string {
  return [a, b].sort().join("-");
}

export default function Agents() {
  const { graph, connected, loading, error } = useAgentGraph();
  const { entries, activeEdges } = roster(graph);
  const live = !graph.empty;

  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-6">
      <div className="mb-6 max-w-2xl">
        <p className="text-sm text-muted-foreground">
          Your AI receptionist is a team of three specialists working a single call. The Concierge
          answers and routes, hands off to Property to search and show homes, and to Scheduling to
          book. Watch the handoff happen live.
        </p>
      </div>

      <div className="mb-4 flex items-center gap-2" data-testid="live-indicator">
        <span
          className={cn(
            "inline-block h-2 w-2 rounded-full",
            live ? "animate-pulse bg-primary" : "bg-muted-foreground/40",
          )}
        />
        <span className="text-sm font-medium">
          {live
            ? graph.liveCalls > 1
              ? `${graph.liveCalls} live calls in progress`
              : "Live call in progress"
            : "No active call"}
        </span>
        {error ? (
          <Badge variant="secondary" className="ml-2">
            offline
          </Badge>
        ) : connected ? (
          <Badge variant="secondary" className="ml-2">
            connected
          </Badge>
        ) : null}
      </div>

      {/* Stage: the SVG edge layer sits behind the absolutely-positioned specialist nodes. */}
      <div className="relative mx-auto h-[360px] w-full rounded-2xl border bg-card">
        <svg
          className="absolute inset-0 h-full w-full"
          aria-hidden="true"
          preserveAspectRatio="none"
        >
          {PAIRS.map(([a, b]) => {
            const on = activeEdges.has(edgeKey(a, b));
            return (
              <line
                key={edgeKey(a, b)}
                data-edge={edgeKey(a, b)}
                data-active={on}
                x1={`${POS[a].x}%`}
                y1={`${POS[a].y}%`}
                x2={`${POS[b].x}%`}
                y2={`${POS[b].y}%`}
                stroke="currentColor"
                strokeWidth={on ? 2.5 : 1.5}
                strokeDasharray={on ? undefined : "5 6"}
                className={cn(
                  on ? "text-primary" : "text-muted-foreground/25",
                  on && "animate-pulse",
                )}
              />
            );
          })}
        </svg>

        {entries.map((e) => (
          <div
            key={e.specialist}
            data-specialist={e.specialist}
            data-active={e.active}
            className="absolute w-40 -translate-x-1/2 -translate-y-1/2 text-center"
            style={{ left: `${POS[e.specialist].x}%`, top: `${POS[e.specialist].y}%` }}
          >
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "relative rounded-full p-1 transition",
                  e.active ? "ring-2 ring-primary ring-offset-2 ring-offset-card" : "",
                )}
              >
                <img
                  src={pickByAgentId(e.specialist)}
                  alt=""
                  className="h-14 w-14 rounded-full bg-muted"
                />
                {e.active ? (
                  <span className="absolute -right-0.5 -top-0.5 h-3.5 w-3.5 animate-pulse rounded-full border-2 border-card bg-primary" />
                ) : null}
              </div>
              <div className="mt-2 text-sm font-semibold">
                {SPECIALIST_LABEL[e.specialist]}
              </div>
              <div className="mt-0.5 text-xs text-muted-foreground">
                {e.active && e.action ? e.action : SPECIALIST_BLURB[e.specialist]}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && !live ? (
        <p className="mt-4 flex items-center justify-center gap-1.5 text-center text-sm text-muted-foreground">
          <Sparkles className="h-4 w-4" />
          Your agents appear here during a live call. Right now your line is quiet.
        </p>
      ) : null}
    </main>
  );
}
