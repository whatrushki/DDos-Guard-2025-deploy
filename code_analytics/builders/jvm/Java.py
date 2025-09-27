from code_analytics.Builder import Builder
from code_analytics.builders.jvm.pipelines.JavaPipeline import JavaRunner
from code_analytics.builders.jvm.pipelines.MavenPipeline import MavenInstaller


class JavaBuilder(Builder):
    IGNORED_DIRS = Builder.IGNORED_DIRS + ['target']  # Специфично для Java

    def _get_base_sections(self) -> dict:
        return {'base': []}  # Multi-stage, обрабатывается в generate_dockerfile

    def generate_dockerfile(self) -> str:
        sections = {'build': [], 'runtime': [], 'cmd': []}
        for component in self.components:
            component.contribute(sections)

        dockerfile_lines = sections['build'] + sections['runtime'] + sections['cmd']
        return "\n".join(dockerfile_lines)

    def detect_components(self):
        self.entry_point = self._detect_entry_point()  # Ищем pom.xml, main class
        self.add_component(MavenInstaller())

    def _detect_entry_point(self) -> str:
        # Простая реализация: предполагаем target/*.jar
        return 'app.jar'  # Доработать: парсить pom.xml для mainClass

    def generate_docker_compose_service(self) -> dict:
        service = super().generate_docker_compose_service()
        service['ports'] = ['8080:8080']  # Для Java по умолчанию
        return service
