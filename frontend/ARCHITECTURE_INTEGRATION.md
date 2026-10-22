# Frontend-Backend Integration Reference (Sneh & Raghav)

## CFG Graph (data.cfg[<fn>]):
- Built by Raghav's `c2f/cfg/cfg_builder.py`.
- Node types (`start`, `end`, `process`, `decision`, `io`): Sneh's custom React Flow components (`FlowNode.jsx`) use these types to render standard flowchart shapes (ovals for start/end, diamonds for decisions, parallelograms for I/O, rectangles for process).
- Decision labels & branches: Conditions ending with `?` and outgoing edges labelled `"TRUE"` and `"FALSE"` feed the flowchart routing.
- Loop back edges & headers: `is_back_edge: true` and `is_loop_header: true` instruct Dagre/React Flow to draw loopback curves.
- Source line links (`lines: [3, 4]`): Powers two-way click-to-highlight between the CodeMirror editor and flowchart nodes.
- Diffing original vs. optimized: Sneh compares `instr_ids` between Raghav's original CFG and Ishani's optimized CFG to grey out or highlight removed code blocks.

## Complexity Metrics (data.metrics[<fn>]):
- Computed by Raghav's `c2f/metrics/complexity.py`.
- Populates the Metrics panel with nodes, edges, decision count, loop count, and cyclomatic complexity ($E - N + 2$).

## API Endpoints & Unified Envelope:
- Maintained in Raghav's `backend/main.py` and `pipeline.py`.
- Sneh's API client (`api/client.js`) calls `/api/tokens`, `/api/ast`, `/api/generate`, and `/api/optimize`, receiving the consistent `{ ok, errors, warnings, data }` HTTP 200 envelope.