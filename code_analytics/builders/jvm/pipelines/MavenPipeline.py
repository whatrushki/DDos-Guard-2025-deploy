from code_analytics.Builder import PipelineComponent


class MavenInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['build'] = [
            "FROM maven:3.9.9-amazoncorretto-17 AS build",
            "WORKDIR /app",
            "COPY . .",
            "RUN mvn clean package -DskipTests"
        ]

        sections['runtime'] = [
            "FROM maven:3.9.9-amazoncorretto-17",
            "WORKDIR /app",
            "COPY --from=build /app .",
            "CMD [\"mvn\", \"exec:java\"]"
        ]