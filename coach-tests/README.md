# Chess Coach test suites

Standalone Node harnesses (no dependencies; `node <file>`, exit 1 on
any failure). They stand up a mock relay + DOM stub and drive the
real page files — they never touch the production gate or any real
password (fixtures use mock credentials only).

Layout mirrors how each suite locates the pages it tests:

- `test-gate-page.mjs` — Standard pages; reads `../coach-you`.
- `../coach-kids/test-kids-page.mjs` — New Player (lives in the
  branch dir; tests its own directory).
- `../coach-beginnertest/test-kids-page.mjs` — New Player mirror.
- `../coach-plans/test-plans-page.mjs` — purchase page (own dir).
- `legacy/test-core.mjs`, `legacy/test-page.mjs` — the pre-relay
  coach page, vendored here (`coach-core.js`, `sf-adapter.js`,
  `coach.js`, `index.html`) so the suites stay runnable; the legacy
  page itself is not deployed.

CI: `.github/workflows/chess-coach.yml` runs all six on pull
requests and on pushes to `main` / `staging`. The same battery is
the deploy gate for the pull-based deployer on Abraham — see
`chess-coach-product/PIPELINE.md`.
