const STATS = [
  {
    figure: "78%",
    body: "of buyers work with the first agent to respond.",
    href: "https://letshackre.com/articles/why-78-percent-buyers-sign-first-agent/",
  },
  {
    figure: "60%",
    body: "of leads arrive after hours.",
    href: "https://www.getaira.io/blog/ai-receptionist-for-real-estate",
  },
  {
    figure: "35 to 46%",
    body: "of inbound calls are missed by agents.",
    href: "https://www.getaira.io/blog/ai-receptionist-for-real-estate",
  },
  {
    figure: "21x",
    body: "more likely to qualify when a lead is answered within 5 minutes.",
    href: "https://hyperleap.ai/blog/real-estate-lead-response-statistics-2026",
  },
];

export function ProofStats() {
  return (
    <section className="border-y border-border bg-accent/30">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <h2 className="text-center text-2xl font-semibold tracking-tight sm:text-3xl">
          Speed and memory decide who wins the lead.
        </h2>
        <dl className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s) => (
            <div key={s.body} className="flex flex-col gap-1">
              <dt className="text-3xl font-semibold text-primary">{s.figure}</dt>
              <dd className="text-sm text-muted-foreground">
                {s.body}{" "}
                <a
                  href={s.href}
                  target="_blank"
                  rel="noreferrer"
                  className="underline underline-offset-2 hover:text-foreground"
                >
                  source
                </a>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
