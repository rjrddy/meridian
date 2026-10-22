# Project-specific interface: Telemetry workbench

Status: accepted. Publication authorized on 2026-10-22.

## Context

The existing portfolio consoles shared a generic dashboard vocabulary. This made unrelated engineering problems look alike and hid the project’s primary object. The user explicitly authorized a visual redesign of the five kept projects.

## Decision

A charcoal-and-phosphor instrument face. Horizontal workbench navigation replaces the fixed sidebar. Monospaced readouts, square controls, measured source health and a gridded full-width trace make the signal the primary object.

Research reference: [Open MCT](https://nasa.github.io/openmct/). Streaming and historical telemetry belong on a continuous inspectable plotting surface.

The plot continues to read actual WebSocket frames; statistics remain derived from received packets. Empty states stay empty until data arrives. No decorative waveform or made-up telemetry.

## Consequences

Maintain an independent visual vocabulary for this project; do not extract a shared cross-repository dashboard template. Preserve action names and API behavior so existing integration flows remain meaningful. Keep measured evidence and explicit hosting limits visible on the public page. Use system fonts and original code-native diagrams to keep the runtime self-contained. Save browser proof separately from the original benchmarks.

See [UI design and verification](../UI.md).
