from code_analytics.Builder import PipelineComponent


class GradleInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['build'] = [
            "FROM gradle:8.10.1-jdk17 AS build",
            "WORKDIR /app",
            "COPY . .",
            "RUN gradle build --no-daemon -x test"
        ]
        sections['runtime'] = [
            "FROM gradle:8.10.1-jdk17",
            "WORKDIR /app",
            "COPY --from=build /app .",
            "CMD [\"gradle\", \"run\"]"
        ]