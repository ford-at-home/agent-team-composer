#!/usr/bin/env node

import { build } from 'esbuild';
import { promises as fs } from 'fs';
import path from 'path';

console.log('🔨 Building CLI bundle...');

// Build the CLI into a single file
await build({
  entryPoints: ['src/cli/index.ts'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  format: 'esm',
  outfile: 'dist/cli-bundle.js',
  external: [
    // Only exclude native modules that can't be bundled
    'fsevents',
    'sharp',
    '@prisma/client'
  ],
  banner: {
    js: 'import { createRequire } from "module";\nconst require = createRequire(import.meta.url);'
  },
  minify: false,
  sourcemap: false
});

// Create wrapper script
const wrapper = `#!/usr/bin/env node
import('./cli-bundle.js');
`;

await fs.writeFile('dist/agent-team-composer', wrapper);
await fs.chmod('dist/agent-team-composer', '755');

console.log('✅ CLI bundle created');