# ---- build ----
FROM node:22-alpine AS build
WORKDIR /app
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
# Use the pnpm version pinned in package.json ("packageManager"), matching local.
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Vite bakes env at build time; the browser calls the backend on the host.
ARG VITE_TOKEN_ENDPOINT=http://localhost:8000/api/v1/token
ARG VITE_AGENT_NAME=assistant
# Clerk publishable key. The signed-in realtor console (overview, listings,
# buyers, settings) needs it; themed-clerk-provider.tsx throws at runtime if it
# is missing, blanking the whole app. Passed through from docker-compose args.
ARG VITE_CLERK_PUBLISHABLE_KEY=
ENV VITE_TOKEN_ENDPOINT=$VITE_TOKEN_ENDPOINT
ENV VITE_AGENT_NAME=$VITE_AGENT_NAME
ENV VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY
RUN pnpm build

# ---- serve ----
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  location / { try_files $uri /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
