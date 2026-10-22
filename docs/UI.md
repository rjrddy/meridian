# Telemetry workbench

## Direction

A charcoal-and-phosphor instrument face. Horizontal workbench navigation replaces the fixed sidebar. Monospaced readouts, square controls, measured source health and a gridded full-width trace make the signal the primary object.

## Outside reference

[Open MCT](https://nasa.github.io/openmct/), inspected on 2026-10-22. Design takeaway: Streaming and historical telemetry belong on a continuous inspectable plotting surface.

This is an original composition and stylesheet. No reference-site code, logos, photographs or proprietary fonts were imported. Fonts use local system stacks; diagrams are original SVG/CSS. No new runtime dependency or third-party request was added.

## Data and behavior

The plot continues to read actual WebSocket frames; statistics remain derived from received packets. Empty states stay empty until data arrives. No decorative waveform or made-up telemetry.

API contracts, authorization, persistence, core algorithms and benchmark datasets were not changed. Existing benchmark outputs remain historical. UI verification and new recordings are saved separately under [docs/results/ui-redesign](results/ui-redesign/).

## Interaction and access

Buttons retain their existing actions and accessible labels. Keyboard focus is visible. Layouts collapse for narrow screens; wide evidence tables scroll inside their own containers. Color is paired with text for status. Motion respects prefers-reduced-motion.

## Review artifacts

- [Actual console](results/ui-redesign/console-desktop.png)
- [Mobile console](results/ui-redesign/console-mobile.png)
- [Browser flow results](results/ui-redesign/browser.json)
- [New console recording](results/ui-redesign/demo.webm)
- [Recording probe](results/ui-redesign/demo-probe.json)
- [Frontend build log](results/ui-redesign/frontend-build.log)

The saved [review-console.py](results/ui-redesign/review-console.py) is the existing real-service browser flow adapted to write into the UI review directory. Run it only against an isolated local demo stack with the normal operator environment configured. Historical performance is not rebenchmarked by this visual review.

## Verification disposition

Final build, lint and existing test suites pass. The redesigned console was exercised against actual isolated local services, not mocked counters. The public-page previews use saved evidence and the new actual recording. The local proof was captured before publication. The repository CI workflow reports the currently pushed revision; README lists the public URL where available.

The initial capture encoded 88.12 seconds and failed the minimum-duration gate; [the raw probe](results/ui-redesign/initial-demo-probe.json) is retained. A longer real capture passed with 96.36 seconds. No frames were padded or fabricated.
