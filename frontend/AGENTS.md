# Prototype Instructions

## GardenTwin decisions

- Backend, simulation equations, and AI implementation are read-only. Frontend changes belong here; do not change the GitHub backend or invent endpoint capabilities.
- Visual truth is ../design-reference/overview-basic.png and overview-advanced.png, supplied by the user. Keep ivory/forest/sage colors, botanical serif headings, the realistic specimen, four linked callouts, editable grid without a house, and the full-width calendar/care rows.
- Main navigation stays Overview, Plant Growth, Soil & Water, Nutrients, Environment. Watering and responsible fertilizer guidance have highest product priority.
- Use a real desktop composition and a mobile reflow. The old mobile mock is outdated; mobile care guidance should come before decorative specimen/grid sections.
- The user wants a local website like Bluebook, with React/HTML/CSS/JSON, Three.js, and selected components/interactions inspired by 21st.dev, Skiper, Cult UI, Watermelon UI, and Motion Primitives. Avoid mixing unrelated visual systems or installing every catalog.
- The Three.js specimen is currently a photographic textured plane. Do not claim it is a scanned 3D model or a plant-health measurement.
- Keep null distinct from zero; preserve units, provenance, artifact relevance, and unknown nutrient/fertilizer states.
- Default JSON is explicitly illustrative. Live forecasts and AI analysis require an actual backend run; no backend currently runs in this workspace.
- Do not push or deploy without a user request. Keep the local preview available.
- Garden layout cells independently retain crop and Basic/Advanced settings in browser storage. Select inspects without modifying cells; Plant copies Garden Setup into an empty cell; Empty removes a plant; Exclude removes the cell from usable space. Editing a selected plant requires an explicit Save plant settings action. No separate crop picker. Crop-specific icons must never misrepresent another species as tomato; full plant images are supplied separately. Leave Plant Growth and API connections unchanged during this layout work.
- A passwordless browser-local profile is required on first use. Its confirmed address/pin coordinates are the shared garden location; edit location through the profile, with no repeated address/latitude/longitude inputs in Basic or Advanced setup. Location changes preserve each plant's crop/soil settings and never relabel existing simulation results. Keep model/API implementation and Plant Growth untouched. Photon provides deliberate address searches; Leaflet/OpenStreetMap provides the map, with visible attribution and honest service errors.

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
