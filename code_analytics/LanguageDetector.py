import os
from enum import Enum
from pathlib import Path
from collections import defaultdict


class ProgrammingLanguage(Enum):
    PYTHON = '.py'
    JAVASCRIPT = '.js'
    JAVA = '.java'
    CPP = '.cpp'
    C = '.c'
    CSHARP = '.cs'
    RUBY = '.rb'
    PHP = '.php'
    HTML = '.html'
    CSS = '.css'
    GO = '.go'
    RUST = '.rs'
    SWIFT = '.swift'
    KOTLIN = '.kt'
    TYPESCRIPT = '.ts'
    UNKNOWN = 'unknown'


def detect_language(file_path: str) -> ProgrammingLanguage:
    """Определяет язык программирования по расширению файла."""
    extension = Path(file_path).suffix.lower()
    for lang in ProgrammingLanguage:
        if lang.value == extension:
            return lang
    return ProgrammingLanguage.UNKNOWN


def analyze_directory(directory_path: str) -> dict:
    """
    Анализирует все файлы в директории и возвращает статистику по языкам программирования.
    Возвращает словарь {язык: количество файлов}.
    """
    if not os.path.isdir(directory_path):
        raise ValueError(f"Указанный путь {directory_path} не является директорией")

    language_counts = defaultdict(int)

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            language = detect_language(file_path)
            language_counts[language.name] += 1

    return dict(language_counts)


def print_language_stats(language_counts: dict):
    """Выводит статистику по найденным языкам программирования."""
    print("\nСтатистика языков программирования:")
    print("-" * 35)
    total_files = sum(language_counts.values())

    if total_files == 0:
        print("Файлы не найдены")
        return

    for language, count in sorted(language_counts.items()):
        percentage = (count / total_files) * 100 if total_files > 0 else 0
        print(f"{language}: {count} файлов ({percentage:.2f}%)")
    print(f"\nВсего файлов: {total_files}")


def main():
    try:
        directory_path = input("Введите путь к директории для анализа: ")
        stats = analyze_directory(directory_path)
        print_language_stats(stats)
    except ValueError as e:
        print(f"Ошибка: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()