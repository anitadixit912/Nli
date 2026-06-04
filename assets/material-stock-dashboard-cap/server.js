'use strict'

const cds = require('@sap/cds')
const path = require('path')
const express = require('express')

// In development, serve the built React UI at /react-ui/
// so Joule Studio's Preview (which appends /react-ui/ to the URL) works correctly.
if (process.env.NODE_ENV !== 'production') {
  cds.on('bootstrap', (app) => {
    const distPath = path.join(__dirname, 'app', 'react-ui', 'dist')
    // Serve static assets (JS, CSS, icons, etc.)
    app.use('/react-ui', express.static(distPath, { index: 'index.html' }))
    // SPA fallback — any /react-ui/* path returns index.html
    app.get('/react-ui/*splat', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'))
    })
  })
}

module.exports = cds.server
