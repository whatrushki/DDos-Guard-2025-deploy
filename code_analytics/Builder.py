import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
import yaml
import fnmatch  # Для игнора паттернов
import re


class Builder(ABC):
    """
    Абстрактный класс для билдеров проектов.
    Оптимизирован для больших проектов: лимит глубины поиска, игнор ненужных директорий.
    Поддерживает модульную сборку через компоненты.
    """

    IGNORED_DIRS = ['.git', 'node_modules', 'venv', '__pycache__', 'target', 'build']  # Расширяемо для языков

    def __init__(self, project_path: str, max_depth: int = 5):
        self.project_path = Path(project_path).resolve()
        if not self.project_path.is_dir():
            raise ValueError(f"Путь {project_path} не является директорией")
        self.components = []
        self.entry_point = None
        self.max_depth = max_depth  # Лимит глубины для поиска в больших проектах
        self.detect_components()

    def _walk_with_depth(self):
        """os.walk с лимитом глубины и игнором директорий."""
        for root, dirs, files in os.walk(self.project_path):
            rel_depth = len(Path(root).relative_to(self.project_path).parts)
            if rel_depth > self.max_depth:
                dirs[:] = []  # Останавливаем углубление
                continue
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
            yield root, dirs, files

    @abstractmethod
    def detect_components(self):
        """Детектим и добавляем необходимые компоненты."""
        pass

    def add_component(self, component):
        self.components.append(component)

    def generate_dockerfile(self) -> str:
        """Собираем Dockerfile из секций."""
        sections = self._get_base_sections()
        sections['install'] = []
        sections['cmd'] = []

        for component in self.components:
            component.contribute(sections)

        dockerfile_lines = sections['base'] + sections['install'] + sections['cmd']
        return "\n".join(dockerfile_lines)

    @abstractmethod
    def _get_base_sections(self) -> dict:
        """Возвращает базовые секции для языка (FROM, WORKDIR)."""
        return {
            'base': [
                "FROM python:3.12-slim",  # Переопределяется в наследниках
                "WORKDIR /app",
                "COPY . /app"
            ]
        }

    def generate_docker_compose_service(self) -> dict:
        """Генерирует конфиг сервиса для docker-compose.yml."""
        service = {
            'build': '.',
            'ports': ['8000:8000'],  # Дефолт, переопределяется
            'volumes': ['./:/app'],
            'environment': []
        }

        for component in self.components:
            component.modify_compose_service(service)

        return service

    def build(self):
        """Генерирует файлы. Для мульти-lang - только сервис, compose в оркестраторе."""
        dockerfile_content = self.generate_dockerfile()
        dockerfile_path = self.project_path / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        print(f"Сгенерирован Dockerfile: {dockerfile_path}")
        return {
            'entry_point': self.entry_point,
            'components': [comp.__class__.__name__ for comp in self.components],
            'dockerfile': str(dockerfile_path),
            'service_config': self.generate_docker_compose_service()
        }


class PipelineComponent(ABC):
    @abstractmethod
    def contribute(self, sections: dict):
        pass

    def modify_compose_service(self, service: dict):
        pass


# Python компоненты (как раньше, но с путями)
class RequirementsInstaller(PipelineComponent):
    def __init__(self, file: str):
        self.file = file

    def contribute(self, sections: dict):
        sections['install'].append(f"RUN pip install --no-cache-dir -r {self.file}")


class PoetryInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['install'].extend([
            "RUN pip install --no-cache-dir poetry",
            "RUN poetry config virtualenvs.create false",
            "RUN poetry install --no-dev --no-interaction --no-ansi"
        ])


class VenvInstaller(PipelineComponent):
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.generate_requirements()

    def generate_requirements(self):
        # Как раньше
        pass  # (сокращено для краткости)

    def contribute(self, sections: dict):
        sections['install'].append("RUN pip install --no-cache-dir -r requirements.txt")


class SimpleRunner(PipelineComponent):
    def __init__(self, entry_point: str):
        self.entry_point = entry_point

    def contribute(self, sections: dict):
        sections['cmd'].append(f'CMD ["python", "{self.entry_point}"]')


class DjangoRunner(PipelineComponent):
    def __init__(self, entry_point: str, settings_module: str):
        self.entry_point = entry_point
        self.settings_module = settings_module

    def contribute(self, sections: dict):
        sections['cmd'].append(
            "RUN pip install Django")
        sections['cmd'].append(
            f"RUN python {self.entry_point} migrate")
        sections['cmd'].append(
            f'CMD ["python", "{self.entry_point}", "runserver", "0.0.0.0:8000"]')  # Не добавляем gunicorn автоматически

    def modify_compose_service(self, service: dict):
        service['environment'].extend([
            f'DJANGO_SETTINGS_MODULE={self.settings_module}',
            'PYTHONUNBUFFERED=1'
        ])


class PythonBuilder(Builder):
    def _get_base_sections(self) -> dict:
        return {
            'base': [
                "FROM python:3.12-slim",
                "WORKDIR /app",
                "COPY . /app"
            ]
        }

    def detect_components(self):
        # Как раньше, но с _walk_with_depth вместо rglob для оптимизации
        self.entry_point, self.settings_module = self._detect_entry_point()
        if 'manage.py' in self.entry_point:
            self.add_component(DjangoRunner(self.entry_point, self.settings_module))
        else:
            self.add_component(SimpleRunner(self.entry_point))

        deps = self._detect_dependencies()
        if deps['type'] == 'requirements':
            self.add_component(RequirementsInstaller(deps['file']))
        elif deps['type'] == 'poetry':
            self.add_component(PoetryInstaller())
        elif deps['type'] == 'venv':
            self.add_component(VenvInstaller(self.project_path))

    def _find_file(self, filename, root, files):
        print(files)
        if filename in files:
            file = Path(root) / filename
            relative_path = file.relative_to(self.project_path).as_posix()
            project_dir = file.parent.name
            if filename == "manage.py":
                settings_module = f"{project_dir}.settings"
            return relative_path, settings_module
        else:
            return None

    def _detect_entry_point(self) -> tuple[str, str]:
        for root, _, files in self._walk_with_depth():
            result = self._find_file("manage.py", root, files)
            if result != None:
                return result

            result = self._find_file("main.py", root, files)
            if result != None:
                return result
            
            if "README.md" in files:
                file = Path(root) / "README.md"
                with open(str(file), 'r') as f:
                    content = f.read()
                search_res = re.search("python .*\.py", content).group(0)
                result = str(search_res).split(" ")[-1]
                return result, None


            # Проверка кандидатов и __main__ аналогично, но в loop
        raise ValueError("Не удалось найти точку входа.")

    def _detect_dependencies(self) -> dict:
        for root, _, files in self._walk_with_depth():
            if 'requirements.txt' in files:
                file = Path(root) / 'requirements.txt'
                return {'type': 'requirements', 'file': file.relative_to(self.project_path).as_posix()}
            # Аналогично для pyproject.toml, venv
        return {'type': 'none'}


# Новый: JavaBuilder с Maven (как пример)
class MavenInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['base'] = [  # Multi-stage
            "FROM maven:3.9.9-amazoncorretto-17 AS build",
            "WORKDIR /app",
            "COPY . /app",
            "RUN mvn clean package -DskipTests"
        ]
        sections['runtime'] = [
            "FROM amazoncorretto:17-alpine-jdk",
            "WORKDIR /app",
            "COPY --from=build /app/target/*.jar /app/app.jar"
        ]
        # Собираем в generate_dockerfile по-другому для multi-stage


class JavaRunner(PipelineComponent):
    def __init__(self, jar_path: str = 'app.jar'):
        self.jar_path = jar_path

    def contribute(self, sections: dict):
        sections['cmd'].append(f'CMD ["java", "-jar", "{self.jar_path}"]')


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
        self.add_component(JavaRunner())

    def _detect_entry_point(self) -> str:
        # Простая реализация: предполагаем target/*.jar
        return 'app.jar'  # Доработать: парсить pom.xml для mainClass

    def generate_docker_compose_service(self) -> dict:
        service = super().generate_docker_compose_service()
        service['ports'] = ['8080:8080']  # Для Java по умолчанию
        return service


class GradleInstaller(PipelineComponent):
    def contribute(self, sections: dict):
        sections['build'] = [
            "FROM gradle:8.10.1-jdk17 AS build",
            "WORKDIR /app",
            "COPY . /app",
            "RUN gradle build --no-daemon -x test"
        ]
        sections['runtime'] = [
            "FROM openjdk:17-slim",
            "WORKDIR /app",
            "COPY --from=build /app/build/libs/*.jar /app/app.jar"
        ]

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
        self.entry_point = deps.get('entry_point', 'app.jar')
        self.add_component(JavaRunner(self.entry_point))

    def _detect_dependencies(self) -> dict:
        for root, _, files in self._walk_with_depth():
            if 'build.gradle' in files or 'build.gradle.kts' in files:
                return {'type': 'gradle', 'entry_point': 'app.jar'}  # Можно парсить build.gradle для точного jar
        return {'type': 'none'}

    def generate_docker_compose_service(self) -> dict:
        service = super().generate_docker_compose_service()
        service['ports'] = ['8080:8080']  # Для Kotlin по умолчанию
        return service


# Пример использования (для теста)
def main():
    try:
        project_path = input("Введите путь к проекту: ")
        # Для теста: builder = PythonBuilder(project_path) или JavaBuilder, etc.
        # Но в реальности используйте оркестратор
    except ValueError as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
