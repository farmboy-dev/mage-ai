# Build the runtime image with Dockerfile_refactor first; both environments share its dependencies.
ARG MAGE_RUNTIME_IMAGE=localhost/mage-fork:dev-base

FROM node:20-bookworm-slim AS frontend
ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    YARN_CACHE_FOLDER=/opt/yarn-cache
WORKDIR /workspace/mage_ai/frontend
COPY mage_ai/frontend/package.json mage_ai/frontend/yarn.lock ./
RUN yarn install --frozen-lockfile --non-interactive
COPY mage_ai/frontend ./
COPY --chmod=0755 scripts/dev/start_frontend.sh /usr/local/bin/mage-dev-frontend
EXPOSE 3000
CMD ["/usr/local/bin/mage-dev-frontend"]

FROM ${MAGE_RUNTIME_IMAGE} AS backend
# PYTHONPATH exposes both mounted source trees, without reinstalling on startup.
# The runtime wheel metadata (including the selected Polars package) stays intact.
ENV PYTHONPATH=/workspace:/workspace/mage_integrations \
    ENV=dev \
    MAGE_DATA_DIR=/var/lib/mage/data
WORKDIR /workspace
COPY mage_ai /workspace/mage_ai
COPY mage_integrations /workspace/mage_integrations
RUN mkdir -p /var/lib/mage
EXPOSE 6789
CMD ["python", "mage_ai/server/server.py", "--host", "0.0.0.0", "--port", "6789", "--project", "/var/lib/mage/project", "--manage-instance", "0"]
