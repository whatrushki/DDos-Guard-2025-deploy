from code_analytics.Builder import PipelineComponent


class YarnInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['build'] = [
            "FROM node:18-alpine AS build",
            "WORKDIR /app",
            "COPY package.json yarn.lock .",
            "RUN yarn install --frozen-lockfile --production"
        ]

        sections['runtime'] = [
            "FROM node:18-alpine",
            "WORKDIR /app",
            "COPY --from=build /app/node_modules ./node_modules",
            "COPY . .",
            "CMD [\"yarn\", \"start\"]"
        ]