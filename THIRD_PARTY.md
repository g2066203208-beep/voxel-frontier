# Third-party components

- three.js 0.186.1, MIT, copyright 2010–2026 three.js authors. Source and license: https://github.com/mrdoob/three.js/blob/dev/LICENSE . Browser viewer uses the npm module.
- occt-import-js 0.0.23, LGPL-2.1. Source and full license: https://github.com/kovacsv/occt-import-js and https://github.com/kovacsv/occt-import-js/blob/main/LICENSE.md . The unmodified npm package runs on the GitHub build runner; its generated tessellation is displayed by the browser. It is not bundled into browser JavaScript. OpenCascade underlies its CAD importer; upstream notices apply.

The reader implementation and dependency versions are available in scripts/read-model.cjs and package-lock.json. Generated geometry retains source hash and import settings in geometry-report.json.
