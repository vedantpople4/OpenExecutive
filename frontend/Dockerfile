# OpenExec web UI: build the SPA, serve it from nginx, and proxy /api to the
# API container on the same box.
#
# Build context is the REPO ROOT so a single .dockerignore governs both images
# and deploy/nginx.conf is in scope:
#
#   docker build -f frontend/Dockerfile -t openexec-web .

FROM node:22-alpine AS build

WORKDIR /src

# Lockfile-only layer first so source edits do not re-run npm ci.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Vite inlines env vars at BUILD time, so this has to be a build arg -- setting
# it on the running container does nothing.
#
# The guard is the important part. src/api/client.ts computes
#   USE_MOCK_API = MODE === 'test' || !API_BASE_URL
# so a build with this unset produces a bundle that silently serves the
# in-memory mock layer: a deployed app showing invented decisions that look
# entirely real. Failing the build is the only honest outcome.
ARG VITE_API_BASE_URL=/api
RUN test -n "$VITE_API_BASE_URL" || { \
      echo "ERROR: VITE_API_BASE_URL is empty. The bundle would fall back to" >&2; \
      echo "       the mock API and serve fabricated data. Refusing to build." >&2; \
      exit 1; \
    }
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build


FROM nginx:alpine

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
