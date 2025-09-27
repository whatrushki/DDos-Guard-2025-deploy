from code_analytics.Builder import Builder
from code_analytics.builders.jvm.pipelines.GradlePipeline import GradleInstaller
from code_analytics.builders.jvm.pipelines.MavenPipeline import MavenInstaller


class KotlinBuilder(Builder):
    IGNORED_DIRS = Builder.IGNORED_DIRS + ['build']  # Специфично для Gradle

    def _get_base_sections(self) -> dict:
        return {'build': [], 'runtime': [], 'cmd': []}  # Для multi-stage

    def generate_dockerfile(self) -> str:
        sections = self._get_base_sections()
        for component in self.components:
            component.contribute(sections)

        dockerfile_lines = sections['build'] + sections['runtime'] + sections['cmd']
        return "\n".join(dockerfile_lines)

    def detect_components(self):
        deps = self._detect_dependencies()
        if deps['type'] == 'gradle':
            self.add_component(GradleInstaller())
        if deps['type'] == 'maven':
            self.add_component(MavenInstaller())

    def _detect_dependencies(self) -> dict:
        for root, _, files in self._walk_with_depth():
            if 'build.gradle' in files or 'build.gradle.kts' in files:
                return {'type': 'gradle'}  # Можно парсить build.gradle для точного jar
        return {'type': 'none'}

    def generate_docker_compose_service(self) -> dict:
        service = super().generate_docker_compose_service()
        service['ports'] = ['8080:8080']  # Для Kotlin по умолчанию
        return service