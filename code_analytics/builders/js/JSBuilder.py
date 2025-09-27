import os

from code_analytics.Builder import Builder
from code_analytics.builders.js.pipelines.NpmBuilder import NpmInstaller
from code_analytics.builders.js.pipelines.Pnpm import PnpmInstaller
from code_analytics.builders.js.pipelines.YarnInstaller import YarnInstaller


class JSBuilder(Builder):
    IGNORED_DIRS = Builder.IGNORED_DIRS + ['node_modules', 'dist', 'build']  # Специфично для JS

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
        if deps['type'] == 'npm':
            self.add_component(NpmInstaller(
                    framework=deps.get('framework'),
                    scripts=deps.get('scripts', {})
                ))
        elif deps['type'] == 'yarn':
            self.add_component(YarnInstaller())
        elif deps['type'] == 'pnpm':
            self.add_component(PnpmInstaller())


    def _detect_dependencies(self) -> dict:
        data = {}
        for root, _, files in self._walk_with_depth():
            vite_configs = ['vite.config.js', 'vite.config.ts', 'vite.config.mjs']
            for config_file in vite_configs:
                if os.path.exists(os.path.join(root, config_file)):
                    data['framework'] = 'vite'

            # Проверяем package.json для определения менеджера пакетов
            if 'package.json' in files:
                if os.path.exists(os.path.join(root, 'yarn.lock')):
                    data['type'] = 'yarn'
                elif os.path.exists(os.path.join(root, 'pnpm-lock.yaml')):
                    data['type'] = 'pnpm'
                elif os.path.exists(os.path.join(root, 'package-lock.json')):
                    data['type'] = 'npm'
                else:
                    data['type'] = 'npm'
                return data

        return {'type': 'none'}

    def generate_docker_compose_service(self) -> dict:
        service = super().generate_docker_compose_service()

        # Для веб-приложений по умолчанию используем порт 3000
        deps = self._detect_dependencies()
        if deps['type'] != 'none':
            service['ports'] = ['3000:3000']  # Для JS по умолчанию (React, Next.js и т.д.)

            # Добавляем hot reload для разработки
            service['environment'] = {
                'CHOKIDAR_USEPOLLING': 'true'
            }
            service['tty'] = True
            service['stdin_open'] = True

        return service
