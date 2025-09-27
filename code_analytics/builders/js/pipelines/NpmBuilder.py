from code_analytics.Builder import PipelineComponent

from code_analytics.Builder import PipelineComponent

from code_analytics.Builder import PipelineComponent


class NpmInstaller(PipelineComponent):
    def __init__(self, framework=None, scripts=None):
        self.framework = framework
        self.scripts = scripts or {}

    def contribute(self, sections: dict):
        sections['build'] = [
            "FROM node:18-alpine",
            "WORKDIR /app",
            "COPY package.json package-lock.json .",
            "RUN cat package.json | grep vite",  # Проверяем зависимости
            "RUN npm install",
            "RUN ls -la node_modules/.bin/ | head -10",  # Смотрим что в .bin
            "RUN which vite || echo 'vite not in PATH'",  # Проверяем PATH
            "RUN find /app -name '*vite*' -type f",  # Ищем все vite файлы
            "COPY . .",
            "EXPOSE 5173",
            "CMD [\"sh\", \"-c\", \"npm run dev -- --host\"]"
        ]
