# GardenTwin frontend

The GardenTwin website lives in this folder. It uses React, TypeScript, Vite, Three.js, Motion, Recharts, Leaflet and Tabler icons. Backend, simulation and AI source files are unchanged by this frontend handoff.

## Open locally

Use Node.js 20.19+ (or 22.12+) and pnpm. From the repository root:

```sh
cd frontend
pnpm install
pnpm dev
```

Open **http://127.0.0.1:5174/**. Keep the same URL when returning: browser storage is separate for `localhost` and `127.0.0.1`.

To verify or build:

```sh
pnpm test
pnpm build
```

The build type-checks the app and writes static assets to `dist/client`. Optional Sites packaging is retained in `dist/server` and `dist/.openai`; no deployment is required to run the app locally.

## Included

- Five tabs: Overview, Plant Growth, Soil & Water, Nutrients and Environment.
- Passwordless first-use profile with a blocked, frosted background; name and a confirmed garden location persist in this browser.
- Photon address search and an optional interactive Leaflet/OpenStreetMap pin picker. These require internet access; no API key is needed for the prototype. Public mapping services have usage limits and no availability guarantee.
- Profile editing through Settings or Garden Setup, with one shared garden location instead of repeated address/coordinate fields.
- Independent saved grid cells. Select inspects; Plant snapshots Garden Setup into an empty cell; Empty removes a plant; Exclude marks unusable space. Edits require **Save plant settings**.
- Crop-specific icons for Tomato, Pepper, Cucumber, Lettuce, Carrot, Bean and Strawberry. The full tomato image is included; other full plant images await supplied assets.
- Daily calendar, watering/fertilizer assessments, weather and growth charts, irrigation comparison, forecast and AI evidence views.
- Desktop and mobile layouts, explicit unknown values, visible units and data provenance.

Profiles and garden layouts are browser-local preferences, not authenticated accounts. Changing the profile location preserves each plant's crop/soil settings and does not relabel old simulation results.

## Existing backend

The app opens with explicitly labeled example data. Its synthetic weather and modeled output are not a successful live backend result.

Run the existing backend separately using the repository's backend instructions. Vite forwards `/api/*` to `http://127.0.0.1:8000/*`. **Analyze garden** sends the form's crop, dates, soil settings and saved profile coordinates through the existing `POST /simulation/run` adapter. Name, area and grid cells are not backend inputs. Grid layout is planning data, not a spatial multi-plant simulation.

Forecast and AI analysis require a real run. Backend runs are held in memory and may disappear after a restart; the frontend handles that case. A production host needs its own API routing: Vite's development proxy is not part of the static build.

Nutrient availability and fertilizer dosage remain unknown when the backend lacks soil-test evidence. Null values are never represented as zero.

The Plant Growth Three.js scene uses a photographic textured plane with illustrative motion, not a rigged 3D plant or measured crop growth. Its existing implementation is preserved.

## Files

- `src/App.tsx`: application state/navigation and profile integration.
- `src/ProfileDialog.tsx`, `profile.ts`, `GardenLocationMap.tsx`, `locationSearch.ts`: profile and location flow.
- `src/gardenLayout.ts`, `GardenSetup.tsx`, `Overview.tsx`: independent cells, setup and overview.
- `src/Details.tsx`, `PlantScene.tsx`, `Charts.tsx`: detailed tabs and specimen.
- `src/api.ts`, `contracts.ts`: existing API adapters/contracts.
- `src/data/`: labeled example fixtures.
- `public/garden/`: included plant/brand/decorative assets and icon licence.
- `tests/`: 21 frontend tests plus four optional hosting packaging checks.
- `COMPONENT_SOURCES.md`: component and asset provenance.

Local backups, dependency folders, build output and private browser profile data are excluded from this handoff.
