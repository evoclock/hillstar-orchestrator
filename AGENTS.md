## How we work

### Where work runs
- All work runs in Herdr/Pi on Julen's machines (MacBook Pro first, then Mac mini, then linux-backend), using his model subscriptions.
- Never use Grok Bot or Cursor cloud compute for this work. Bots only brief, spawn and check Pi workers.
- Never serve models via llama.cpp. Use the existing MLX serve setup or TensorFold.

### Design before build
- Required for major work and for initial work on a repo or feature.
- A refactor likely to affect other parts of a repo runs the `blast-radius` skill alongside the design.
- Small fixes (a one-line CI tweak, a typo) skip the design step.
- Every repo keeps a TLA+ model and a spec. Check a change against them first to size the work before building.

For work that needs design, pi-bowerbird produces:
1. a diagram;
2. a spec;
3. a TLA+ model, checked with TLC before any code is written;
4. a short readable document that explains the solution to Julen.

Then check the design with the pi-poteto-mode `statechart` skill.

### Build
- Build with skills from pi-poteto-mode, pi-agentic-driver and the other installed packs.
- Don't redo by hand what a skill already covers.

### Worktrees
- Lease every worktree from Treehouse.
- After a merge, recycle the worktree and return the lease. Never edit in a plain checkout.

### Merges and releases
- Agents may push to any repo.
- Public main merges are Julen's when he's present. Private repos may merge on green.
- Releases are Julen's only.
