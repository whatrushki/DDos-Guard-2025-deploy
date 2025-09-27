from code_analytics.Builder import PipelineComponent


class PnpmInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['build'] = [
            "FROM node:18-alpine AS build",
            "WORKDIR /app",
            "RUN npm install -g pnpm",
            "COPY package.json pnpm-lock.yaml .",
            "RUN pnpm install --frozen-lockfile --prod"
        ]

        sections['runtime'] = [
            "FROM node:18-alpine",
            "WORKDIR /app",
            "RUN npm install -g pnpm",
            "COPY --from=build /app/node_modules ./node_modules",
            "COPY . .",
            "CMD [\"pnpm\", \"start\"]"
        ]
