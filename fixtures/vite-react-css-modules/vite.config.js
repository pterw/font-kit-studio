// CSS HMR is enough for this corpus; no React Fast Refresh plugin is installed.
export default {
  // Keep module exports stable when declaration values change during CSS HMR.
  css: { modules: { generateScopedName: '[name]__[local]___[hash:base64:5]' } },
  server: { host: '127.0.0.1', port: 0 },
};
