import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { getLiveListings, getListingMatches, type MatchReport } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Shows, for the realtor's newest connected listing, which remembered buyers want it. This is
// Cognee graph matching made visible: add a home, see who is waiting for it.
export function MatchCard() {
  const [address, setAddress] = useState<string>("");
  const [report, setReport] = useState<MatchReport | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const listings = await getLiveListings();
        const newest = listings[0];
        if (!newest?.code || !active) return;
        setAddress(newest.address ?? newest.code);
        const matches = await getListingMatches(newest.code);
        if (!active) return;
        setReport(matches);
      } catch {
        // best effort; the card just stays empty
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  if (!report) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="size-4 text-primary" /> Buyers waiting
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="truncate text-muted-foreground">{address}</span>
          <Badge variant={report.count > 0 ? "success" : "muted"}>
            {report.count} match{report.count === 1 ? "" : "es"}
          </Badge>
        </div>
        {report.buyers.map((b, i) => (
          <div key={b.phone ?? b.name ?? i} className="text-foreground">
            {b.name}
          </div>
        ))}
        {report.count > 0 && (
          <p className="text-xs text-muted-foreground">{report.narrative}</p>
        )}
      </CardContent>
    </Card>
  );
}
