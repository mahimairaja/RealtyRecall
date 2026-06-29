<p align="center">
  <img src="assets/banner.png" alt="RealtyRecall" width="100%" />
</p>

<h1 align="center">RealtyRecall</h1>

<p align="center">
  <b>The always-on voice assistant for solo real estate agents that never forgets a buyer.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/HangOver-Cognee_Hackathon-1f96aa" alt="Cognee Hackathon" />
  <img src="https://img.shields.io/badge/voice-LiveKit-1fb6c9" alt="LiveKit" />
  <img src="https://img.shields.io/badge/memory-Cognee-7c4dff" alt="Cognee" />
  <img src="https://img.shields.io/badge/python-3.11+-3776AB" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT" />
  <img src="https://img.shields.io/badge/%23buildinpublic-day_1-ff6b35" alt="Build in public" />
</p>

---

RealtyRecall answers every call in your name, qualifies the buyer, books the showing, and remembers every buyer and every listing across calls. Connect your listings in minutes, then let it carry the context no answering service can: a returning buyer is greeted by name and picks up exactly where they left off, and it gets sharper with every conversation.

Built for solo agents who lose leads to missed calls, and who are tired of receptionist bots that forget the caller the second they hang up.

> Built in public for The Hangover Part AI, the Cognee memory hackathon (Jun 29 to Jul 5, 2026). Live at [hangover.mahimai.ca](https://hangover.mahimai.ca).

## How it works

1. Connect listings. Paste your listings page or upload a file. RealtyRecall reads your homes into a memory graph in under a minute.
2. Buyer calls. The assistant answers around the clock, qualifies budget, timeline, financing, and area, and recalls the homes that match.
3. Books the showing. On your calendar, then texts you the lead.
4. Never forgets. Every buyer and listing lives in a knowledge graph, so memory carries across calls and improves over time.

## Why memory changes everything

Most AI receptionists are stateless: they forget the caller the moment the line drops. RealtyRecall runs on a hybrid graph and vector memory powered by [Cognee](https://github.com/topoteretes/cognee) (self-hosted, open source). Four operations run the whole product:

- remember: ingest the realtor's listings and each buyer
- recall: match a buyer to the right homes, across sessions
- improve: sharpen the memory after every call
- forget: remove a buyer on request

## Topics

- The problem: missed calls and amnesiac receptionists
- The two magic moments: instant listing onboarding, and memory across calls
- Architecture: the voice loop and the memory layer
- The memory model: realtor, listing, neighbourhood, buyer, showing
- Legal data posture: your own listings with consent (official feeds later)
- Quickstart: run it locally
- Demo: hear it answer real listings
- Roadmap: phone numbers, official listing feeds, more verticals
- Build log: daily updates on LinkedIn and X

## Stack

Voice: LiveKit Agents, Deepgram, OpenAI, Cartesia. Memory: Cognee. Backend: FastAPI. Frontend: React. Booking: cal.com. Texts: Telnyx.

## Status

Work in progress, day 1 of 7. Watch this repo, or follow the build on [LinkedIn](https://www.linkedin.com/in/mahimairaja/) and [X](https://x.com/mahimaidev).

## License

MIT. See [LICENSE](LICENSE).
