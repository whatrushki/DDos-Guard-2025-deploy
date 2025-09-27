# 🚀 AutoDeploy: Автоматизация развертывания приложений на разных языках

> **Цель проекта** — упростить и автоматизировать процесс развертывания приложений, написанных на различных языках программирования, через унифицированный интерфейс.

---

## 📁 Структура проекта

code_analytics/
├── builders/               # Классы-строитель для каждого языка (например, JSBuilder, JavaBuilder)
│   ├── js/
│   │   └── pipelines/      # Пайплайны сборки JS (npm, yarn, pnpm)
│   └── jvm/
│       └── pipelines/      # Пайплайны сборки JVM (Maven, Gradle)
├── pipelines/              # Основные пайплайны и классы-оркестраторы
│   ├── Builder.py          # Базовый класс Builder
│   ├── LanguageDetector.py # Определение языка по коду
│   ├── Orchestrator.py     # Управление цепочкой сборки и запуска
│   ├── Java.py             # Реализация для Java
│   ├── Kotlin.py           # Реализация для Kotlin
│   ├── MavenPipeline.py    # Пайплайн Maven
│   ├── GradlePipeline.py   # Пайплайн Gradle
│   └── ...                 # Другие пайплайны
├── gui/                    # Графический интерфейс пользователя
│   ├── app.py              # 🎯 Главная точка входа
│   ├── main.py             # Запуск GUI
│   ├── ConnectionManager.py
│   ├── SFTPManager.py
│   └── SSHManager.py
├── generated_files/        # Сгенерированные файлы (Dockerfile, docker-compose.yml и т.д.)
├── requirements.txt        # Зависимости Python
├── LICENSE
└── README.md

## ⚙️ Как запустить проект

1. Установите зависимости:

```bash
pip install -r requirements.txt

2. Запустите приложение:
python gui/app.py

## ➕ Как добавить поддержку нового языка 

Чтобы расширить функциональность и добавить поддержку нового языка (например, Python, Rust, Go): 

    Создайте новую директорию в builders/ (например, builders/python/)
    Внутри создайте модуль pipelines/, содержащий классы-пайплайны (например, PipBuilder.py, PoetryBuilder.py)
    Реализуйте класс Runner и Builder для языка, унаследовав их от базовых классов в pipelines/Builder.py
    Добавьте логику определения языка в pipelines/LanguageDetector.py
    Обновите pipelines/Orchestrator.py, чтобы он мог обрабатывать новый язык
     
