#!/bin/sh
set -eu

# Refresh the dependency volume from the image's Yarn cache, without a registry fetch.
# Rebuild the frontend image when package.json or yarn.lock dependencies change.
yarn install --offline --frozen-lockfile --non-interactive
exec yarn dev --hostname 0.0.0.0 --port 3000
