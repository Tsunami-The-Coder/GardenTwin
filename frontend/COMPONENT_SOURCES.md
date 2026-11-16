# Component and asset sources

The user's visual reference is authoritative. External catalogs were reviewed as implementation references, with a single GardenTwin visual system retained.

- [21st.dev](https://21st.dev/): component/navigation references.
- [Skiper UI](https://skiper-ui.com/): interaction and component references.
- [Cult UI](https://www.cult-ui.com/): component and chart references.
- [Watermelon UI](https://ui.watermelon.sh/): React dashboard and composition references.
- [Motion Primitives](https://motion-primitives.com/): requested motion reference; its pages returned 403 to the web reader. The implementation uses the documented [Motion React](https://motion.dev/docs/react) core library for transitions.
- [Three.js](https://threejs.org/manual/pages/creating-a-scene.html) and [texture documentation](https://threejs.org/manual/pages/textures.html): actual scene, camera, renderer, texture and lifecycle implementation.
- [Tabler Icons](https://tabler.io/icons): consistent outline UI icons. MIT notice is in `public/garden/TABLER-LICENSE.txt`.
- [DM Sans](https://fonts.google.com/specimen/DM+Sans): interface font. Georgia is the system serif fallback/display face.

No code is represented as imported from every catalog. The app uses local components, selected library dependencies, and the provided art direction. A specific catalog component can be added without replacing the visual system.

The plant, tomato marker and wordmark were recovered from the user's previous generated assets. A clean sage-arc background was generated during this task. The original design references are preserved in the workspace's `design-reference/` folder.
