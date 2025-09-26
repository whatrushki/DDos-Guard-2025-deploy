import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Type

import yaml

# Импортируем из предыдущих скриптов
# Предполагаем, что analyze_code_languages.py и deployment_builder.py в той же директории
from LanguageDetector import analyze_directory, ProgrammingLanguage
from Builder import Builder, PythonBuilder, JavaBuilder, KotlinBuilder

# Маппинг языков к их билдерам
BUILDER_MAPPING: Dict[ProgrammingLanguage, Type[Builder]] = {
    ProgrammingLanguage.PYTHON: PythonBuilder,
    ProgrammingLanguage.JAVA: JavaBuilder,
    ProgrammingLanguage.KOTLIN: KotlinBuilder,
}


class DeploymentOrchestrator:
    """
    Посредник между анализатором языков и билдерами.
    Анализирует языки в проекте, выбирает соответствующие билдеры и запускает их.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        if not self.project_path.is_dir():
            raise ValueError(f"Путь {project_path} не является директорией")

    def get_languages(self) -> dict:
        """Получает статистику языков из анализатора."""
        return analyze_directory(str(self.project_path))

    def select_builders(self, languages: dict) -> list:
        """Выбирает и инициализирует билдеры для обнаруженных языков."""
        builders = []
        for lang_name, count in languages.items():
            if count > 0 and lang_name != 'UNKNOWN':
                try:
                    lang_enum = ProgrammingLanguage[lang_name]
                    if lang_enum in BUILDER_MAPPING:
                        builder_class = BUILDER_MAPPING[lang_enum]
                        builder = builder_class(str(self.project_path))
                        builders.append(builder)
                except KeyError:
                    print(f"Язык {lang_name} не поддерживается для билдера.")
        return builders

    def orchestrate(self):
        languages = self.get_languages()
        print("\nОбнаруженные языки:", languages)

        builders = self.select_builders(languages)
        if not builders:
            return

        compose_data = {
            'version': '3.8',
            'services': {}
        }

        results = []
        for i, builder in enumerate(builders):
            lang_name = builder.__class__.__name__.replace('Builder', '').lower()
            result = builder.build()
            service_name = f'app-{lang_name}' if len(builders) > 1 else 'app'
            compose_data['services'][service_name] = result['service_config']
            results.append(result)

        if builders:
            compose_path = self.project_path / 'docker-compose.yml'
            with open(compose_path, 'w') as f:
                f.write(yaml.dump(compose_data, default_flow_style=False))
            print(f"Сгенерирован docker-compose.yml: {compose_path}")

        return results


def main():
    try:
        project_path = input("Введите путь к проекту для оркестрации развертывания: ")
        orchestrator = DeploymentOrchestrator(project_path)
        results = orchestrator.orchestrate()
        if results:
            print("\nРезультаты развертывания:")
            for res in results:
                print(res)
    except ValueError as e:
        print(f"Ошибка: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
