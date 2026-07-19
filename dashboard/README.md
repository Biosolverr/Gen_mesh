# GenMesh Core - Control Panel

One file, `index.html`, zero build step, zero dependencies besides
`genlayer-js`, loaded straight from a CDN in the browser. It gives
direct access to every read/write method on all six mesh contracts,
connected directly to studionet — no backend in between. Everything the
panel shows was pulled directly from the network at call time.

## What's Inside

- Session — a field for a studionet private key. Only needed for
  write methods (registering an agent, submitting a task, etc.); reads
  work without it. The key lives only in the tab's memory, never goes
  into `localStorage`, and is cleared on reload.
- **Contract Addresses** — six fields (Registry, Coordinator,
  Aggregator, three agents), saved to the browser's `localStorage`.
- **Full Pipeline** — one-button `submit_task` + manual `get_result`
  polling, so you don't have to click through every method individually
  for the typical scenario.
- One section per contract — a card for every method: Read gets a
  "Call" button, Write gets "Send Transaction," each with its own
  result area. Write buttons share a single lock — only one signed
  transaction goes out at a time, since every write shares the same
  signing account and nonce sequence.
- Activity Log — history of every call made from this panel: time,
  contract, method, arguments, status (`pending → accepted →
  finalized`/`error`), and for write calls, a real transaction hash
  with a clickable link to `explorer-studio.genlayer.com`. Stored in
  `localStorage` (last 100 entries), survives a page reload.

## Deploying to Vercel (free)

A static file — Vercel detects `index.html` at the root with zero
configuration; no `package.json` or build command needed.

**Option A — via Vercel CLI:**
```bash
npm i -g vercel
cd dashboard
vercel
```
`vercel --prod` for the production alias.

**Option B — via GitHub + the Vercel dashboard:**
1. Push the repository to GitHub.
2. On vercel.com → Add New Project → Import Git Repository.
3. **Root Directory** → set to `dashboard` (important if you're pushing
   the whole `genmesh-core` repo rather than just this folder).
4. Framework Preset — "Other" / auto-detect. Deploy — no environment
   variables needed.

Both options fit within the free Vercel Hobby plan.

## Known Limitation

The panel only works with studionet (`genlayer-js/chains` →
`studionet` is hardcoded inside `index.html`) — GenLayer doesn't have a
testnet/mainnet yet at the time of writing, so this wasn't built out
ahead of that need.
