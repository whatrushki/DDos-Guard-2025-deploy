import json
import os
import shutil
import tempfile
from io import StringIO

import flet as ft
import paramiko

from GitManager import GitManager
from SFTPManager import SFTPManager
from SSHManager import SSHManager
from code_analytics.Orchestrator import DeploymentOrchestrator

# Конфигурация по умолчанию для тестирования
DEFAULT_CONFIG = {
    "git_url": "https://github.com/NekrasovVM/Bitrix.git",
    "branch": "main",
    "host": "172.18.31.66",
    "port": "22",
    "username": "kriti",
    "auth_method": "password",
    "password": "12356",
    "ssh_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
    "deploy_path": "./ftp"
}


class AdvancedGitDeployerApp:
    def __init__(self, use_default_config=False):
        self.page = None
        self.temp_dir = None
        self.current_project_path = None
        self.use_default_config = use_default_config

        # Конфиг для быстрого тестирования
        self.test_config = DEFAULT_CONFIG

    async def main(self, page: ft.Page):
        self.page = page
        page.title = "Advanced Git Deployer with Orchestration"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.scroll = ft.ScrollMode.ADAPTIVE

        # Элементы интерфейса
        self.git_url = ft.TextField(
            label="Git Repository URL",
            hint_text="https://github.com/username/repo.git",
            width=400,
            value=self.test_config["git_url"] if self.use_default_config else ""
        )

        self.branch = ft.TextField(
            label="Branch (optional)",
            hint_text="main, develop, etc.",
            width=200,
            value=self.test_config["branch"] if self.use_default_config else ""
        )

        self.host = ft.TextField(
            label="Remote Host",
            hint_text="192.168.1.100 or domain.com",
            width=300,
            value=self.test_config["host"] if self.use_default_config else ""
        )

        self.port = ft.TextField(
            label="SSH Port",
            value=self.test_config["port"] if self.use_default_config else "22",
            width=100
        )

        self.username = ft.TextField(
            label="Username",
            hint_text="root, ubuntu, etc.",
            width=200,
            value=self.test_config["username"] if self.use_default_config else ""
        )

        self.auth_method = ft.Dropdown(
            label="Authentication Method",
            options=[
                ft.dropdown.Option("password"),
                ft.dropdown.Option("ssh_key")
            ],
            value=self.test_config["auth_method"] if self.use_default_config else "password",
            width=200
        )

        self.password = ft.TextField(
            label="Password",
            password=True,
            width=300,
            value=self.test_config["password"] if self.use_default_config and self.test_config[
                "auth_method"] == "password" else "",
            visible=self.test_config["auth_method"] == "password" if self.use_default_config else True
        )

        self.ssh_key = ft.TextField(
            label="SSH Private Key",
            multiline=True,
            min_lines=4,
            max_lines=8,
            width=400,
            value=self.test_config["ssh_key"] if self.use_default_config and self.test_config[
                "auth_method"] == "ssh_key" else "",
            visible=self.test_config["auth_method"] == "ssh_key" if self.use_default_config else False
        )

        self.deploy_path = ft.TextField(
            label="Deploy Path on Remote",
            value=self.test_config["deploy_path"] if self.use_default_config else "/opt/app",
            width=300
        )

        # Кнопка для загрузки/сохранения конфига
        self.config_buttons = ft.Row([
            ft.ElevatedButton(
                "Save Config",
                icon=ft.Icons.SAVE,
                on_click=self.save_config
            ),
            ft.ElevatedButton(
                "Load Config",
                icon=ft.Icons.UPLOAD,
                on_click=self.load_config
            ),
            ft.ElevatedButton(
                "Use Test Config",
                icon=ft.Icons.PLAY_ARROW,
                on_click=self.use_test_config
            )
        ])

        # Логи и вывод
        self.log_output = ft.TextField(
            label="Deployment Log",
            multiline=True,
            min_lines=12,
            max_lines=20,
            read_only=True,
            width=600
        )

        self.progress_bar = ft.ProgressBar(
            width=600,
            visible=False
        )

        self.status_text = ft.Text(
            "Ready to deploy" if not self.use_default_config else "Test config loaded - ready for testing",
            color=ft.Colors.BLUE
        )

        # Кнопки действий
        self.full_deploy_btn = ft.ElevatedButton(
            "Full Deployment",
            icon=ft.Icons.DESCRIPTION,
            on_click=self.full_deployment,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN)
        )

        self.orchestrate_btn = ft.ElevatedButton(
            "Analyze & Generate",
            icon=ft.Icons.ANALYTICS,
            on_click=self.analyze_and_generate
        )

        self.transfer_btn = ft.ElevatedButton(
            "Transfer Files",
            icon=ft.Icons.UPLOAD,
            on_click=self.transfer_files
        )

        self.deploy_remote_btn = ft.ElevatedButton(
            "Deploy on Remote",
            icon=ft.Icons.CLOUD,
            on_click=self.deploy_on_remote
        )

        self.test_ssh_btn = ft.ElevatedButton(
            "Test SSH",
            icon=ft.Icons.LINK,
            on_click=self.test_ssh_connection
        )

        self.clear_log_btn = ft.ElevatedButton(
            "Clear Log",
            icon=ft.Icons.CLEAR,
            on_click=self.clear_log
        )

        # Обработчик изменения метода аутентификации
        self.auth_method.on_change = self.on_auth_method_change

        # Макет приложения
        page.add(
            ft.Column([
                ft.Text("Advanced Git Deployer", size=24, weight=ft.FontWeight.BOLD),

                # Панель управления конфигурацией
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Configuration Management", size=16, weight=ft.FontWeight.BOLD),
                            self.config_buttons,
                        ]),
                        padding=10
                    )
                ),

                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Git Repository", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([self.git_url, self.branch]),
                        ]),
                        padding=15
                    )
                ),

                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Remote Server", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([self.host, self.port, self.username]),
                            ft.Row([self.auth_method, self.deploy_path]),
                            self.password,
                            self.ssh_key,
                        ]),
                        padding=15
                    )
                ),

                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Deployment Steps", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                self.orchestrate_btn,
                                self.transfer_btn,
                                self.deploy_remote_btn,
                            ]),
                            ft.Row([
                                self.full_deploy_btn,
                                self.test_ssh_btn,
                                self.clear_log_btn,
                            ]),
                        ]),
                        padding=15
                    )
                ),

                self.status_text,
                self.progress_bar,
                self.log_output,
            ])
        )

    async def on_auth_method_change(self, e):
        """Обрабатывает изменение метода аутентификации"""
        if self.auth_method.value == "password":
            self.password.visible = True
            self.ssh_key.visible = False
        else:
            self.password.visible = False
            self.ssh_key.visible = True

        self.page.update()

    async def save_config(self, e):
        """Сохраняет текущую конфигурацию в файл"""
        try:
            config = {
                "git_url": self.git_url.value,
                "branch": self.branch.value,
                "host": self.host.value,
                "port": self.port.value,
                "username": self.username.value,
                "auth_method": self.auth_method.value,
                "password": self.password.value if self.auth_method.value == "password" else "",
                "ssh_key": self.ssh_key.value if self.auth_method.value == "ssh_key" else "",
                "deploy_path": self.deploy_path.value
            }

            with open("deploy_config.json", "w") as f:
                json.dump(config, f, indent=2)

            await self.log_message("✅ Configuration saved to deploy_config.json")
        except Exception as ex:
            await self.log_message(f"❌ Error saving config: {str(ex)}")

    async def load_config(self, e):
        """Загружает конфигурацию из файла"""
        try:
            if os.path.exists("deploy_config.json"):
                with open("deploy_config.json", "r") as f:
                    config = json.load(f)

                self.git_url.value = config.get("git_url", "")
                self.branch.value = config.get("branch", "")
                self.host.value = config.get("host", "")
                self.port.value = config.get("port", "22")
                self.username.value = config.get("username", "")
                self.auth_method.value = config.get("auth_method", "password")
                self.deploy_path.value = config.get("deploy_path", "/opt/app")

                if self.auth_method.value == "password":
                    self.password.value = config.get("password", "")
                else:
                    self.ssh_key.value = config.get("ssh_key", "")

                await self.on_auth_method_change(None)
                self.page.update()
                await self.log_message("✅ Configuration loaded from deploy_config.json")
            else:
                await self.log_message("❌ Config file not found")
        except Exception as ex:
            await self.log_message(f"❌ Error loading config: {str(ex)}")

    async def use_test_config(self, e):
        """Загружает тестовую конфигурацию"""
        try:
            self.git_url.value = self.test_config["git_url"]
            self.branch.value = self.test_config["branch"]
            self.host.value = self.test_config["host"]
            self.port.value = self.test_config["port"]
            self.username.value = self.test_config["username"]
            self.auth_method.value = self.test_config["auth_method"]
            self.deploy_path.value = self.test_config["deploy_path"]

            if self.auth_method.value == "password":
                self.password.value = self.test_config["password"]
            else:
                self.ssh_key.value = self.test_config["ssh_key"]

            await self.on_auth_method_change(None)
            self.page.update()
            await self.log_message("✅ Test configuration loaded. Ready for testing!")
        except Exception as ex:
            await self.log_message(f"❌ Error loading test config: {str(ex)}")

    async def log_message(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_output.value += f"{message}\n"
        self.log_output.update()
        self.page.update()

    async def clear_log(self, e):
        """Очищает лог"""
        self.log_output.value = ""
        self.log_output.update()

    async def set_loading(self, loading: bool):
        """Включает/выключает индикатор загрузки"""
        self.progress_bar.visible = loading
        self.full_deploy_btn.disabled = loading
        self.orchestrate_btn.disabled = loading
        self.transfer_btn.disabled = loading
        self.deploy_remote_btn.disabled = loading
        self.config_buttons.disabled = loading
        self.page.update()

    async def set_status(self, message: str, color=ft.Colors.BLUE):
        """Устанавливает статус"""
        self.status_text.value = message
        self.status_text.color = color
        self.status_text.update()

    # Остальные методы (full_deployment, analyze_and_generate, transfer_files, deploy_on_remote, test_ssh_connection)
    # остаются без изменений, как в предыдущей версии

    async def test_ssh_connection(self, e):
        """Тестирует SSH соединение"""
        await self.set_loading(True)
        await self.set_status("Testing SSH connection...")

        try:
            secret = self.password.value if self.auth_method.value == "password" else self.ssh_key.value

            # Используем paramiko для тестирования соединения
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_params = {
                'hostname': self.host.value,
                'username': self.username.value,
                'port': int(self.port.value) if self.port.value else 22,
            }

            if self.auth_method.value == "password":
                connect_params['password'] = secret
            else:
                private_key = paramiko.RSAKey.from_private_key(StringIO(secret))
                connect_params['pkey'] = private_key

            await self.log_message("🔌 Testing SSH connection...")
            ssh.connect(**connect_params, timeout=10)

            # Выполняем простую команду для проверки
            stdin, stdout, stderr = ssh.exec_command('uname -a')
            result = stdout.read().decode().strip()

            await self.log_message(f"✅ SSH connection successful!")
            await self.log_message(f"💻 System info: {result}")

            ssh.close()
            await self.set_status("SSH connection successful!", ft.Colors.GREEN)

        except Exception as ex:
            await self.log_message(f"❌ SSH connection failed: {str(ex)}")
            await self.set_status("SSH connection failed!", ft.Colors.RED)
        finally:
            await self.set_loading(False)

    async def on_auth_method_change(self, e):
        """Обрабатывает изменение метода аутентификации"""
        if self.auth_method.value == "password":
            self.password.visible = True
            self.ssh_key.visible = False
        else:
            self.password.visible = False
            self.ssh_key.visible = True

        self.page.update()

    async def log_message(self, message: str, color=ft.Colors.BLACK):
        """Добавляет сообщение в лог"""
        self.log_output.value += f"{message}\n"
        self.log_output.update()
        self.page.update()

    async def clear_log(self, e):
        """Очищает лог"""
        self.log_output.value = ""
        self.log_output.update()

    async def set_loading(self, loading: bool):
        """Включает/выключает индикатор загрузки"""
        self.progress_bar.visible = loading
        self.full_deploy_btn.disabled = loading
        self.orchestrate_btn.disabled = loading
        self.transfer_btn.disabled = loading
        self.deploy_remote_btn.disabled = loading
        self.page.update()

    async def set_status(self, message: str, color=ft.Colors.BLUE):
        """Устанавливает статус"""
        self.status_text.value = message
        self.status_text.color = color
        self.status_text.update()

    async def full_deployment(self, e):
        """Полный процесс деплоя"""
        await self.set_loading(True)
        await self.set_status("Starting full deployment...")

        # try:
        # 1. Клонирование
        await self.log_message("=== STEP 1: Cloning Repository ===")
        if not await self.clone_repository():
            return

        # 2. Анализ и генерация
        await self.log_message("=== STEP 2: Analysis & Generation ===")
        if not await self.analyze_and_generate_internal():
            return

        # 3. Передача файлов
        await self.log_message("=== STEP 3: File Transfer ===")
        if not await self.transfer_files_internal():
            return

        # 4. Деплой на удаленной машине
        await self.log_message("=== STEP 4: Remote Deployment ===")
        if not await self.deploy_on_remote_internal():
            return

        await self.set_status("Deployment completed successfully!", ft.Colors.GREEN)
        await self.log_message("✅ Full deployment completed!")

    # except Exception as ex:
    #     await self.set_status("Deployment failed!", ft.Colors.RED)
    #     await self.log_message(f"❌ Deployment error: {str(ex)}")
    # finally:
    #     await self.set_loading(False)

    async def analyze_and_generate(self, e):
        """Только анализ и генерация"""
        await self.set_loading(True)
        await self.analyze_and_generate_internal()
        await self.set_loading(False)

    async def analyze_and_generate_internal(self):
        """Внутренняя логика анализа и генерации"""
        try:
            if not self.current_project_path:
                await self.log_message("❌ Please clone repository first")
                return False

            await self.log_message("🔍 Analyzing project structure...")

            # Используем ваш оркестратор
            orchestrator = DeploymentOrchestrator(self.current_project_path)

            await self.log_message("📊 Detecting programming languages...")
            languages = orchestrator.get_languages()
            await self.log_message(f"📋 Detected languages: {languages}")

            await self.log_message("🏗️ Generating deployment pipelines...")
            results = orchestrator.orchestrate()

            if results:
                await self.log_message("✅ Dockerfile and docker-compose.yml generated successfully!")

                # Проверяем сгенерированные файлы
                dockerfile_path = os.path.join(self.current_project_path, "Dockerfile")
                compose_path = os.path.join(self.current_project_path, "docker-compose.yml")

                if os.path.exists(dockerfile_path):
                    await self.log_message(f"📄 Dockerfile: {dockerfile_path}")
                if os.path.exists(compose_path):
                    await self.log_message(f"📄 docker-compose.yml: {compose_path}")

                return True
            else:
                await self.log_message("❌ Failed to generate deployment files")
                return False

        except Exception as ex:
            await self.log_message(f"❌ Analysis error: {str(ex)}")
            return False

    async def transfer_files(self, e):
        """Только передача файлов"""
        await self.set_loading(True)
        await self.transfer_files_internal()
        await self.set_loading(False)

    async def transfer_files_internal(self):
        # """Внутренняя логика передачи файлов"""
        # try:
        if not self.current_project_path:
            await self.log_message("❌ No project to transfer")
            return False

        await self.log_message("📤 Transferring files to remote server...")

        # Используем ваш SFTPManager
        secret = self.password.value if self.auth_method.value == "password" else self.ssh_key.value

        # Создаем директорию на удаленной машине
        ssh_manager = SSHManager(
            host=self.host.value,
            user=self.username.value,
            secret=secret,
            port=int(self.port.value) if self.port.value else 22
        )

        ssh_manager.open_connection()

        _, std, _ = ssh_manager.execute_command("uname -a")
        std_str = ""
        for line in iter(std.readline, ""):
            std_str += line

        host = 'linux' if 'linux' in std_str.lower() else 'windows'
        slash = '/' if host == 'linux' else '\\'

        sftp_manager = SFTPManager(
            host=self.host.value,
            user=self.username.value,
            secret=secret,
            port=int(self.port.value) if self.port.value else 22,
            host_os=host
        )

        sftp_manager.open_connection()

        if not sftp_manager.is_connection_opened():
            await self.log_message("❌ SFTP connection failed")
            return False

        self.root = self.deploy_path.value + slash + self.git_url.value.split('/')[-1].replace('.git', '')

        ssh_manager.execute_command(
            f"""cd {self.deploy_path.value}
             git clone {self.git_url.value}"""
        )

        sftp_manager.upload_files(self.current_project_path, self.root)

        sftp_manager.close_connection()
        ssh_manager.close_connection()

        await self.log_message("✅ Files transferred successfully!")
        return True

    #
    # except Exception as ex:
    #     await self.log_message(f"❌ File transfer error: {str(ex)}")
    #     return False

    async def deploy_on_remote(self, e):
        """Только деплой на удаленной машине"""
        await self.set_loading(True)
        await self.deploy_on_remote_internal()
        await self.set_loading(False)

    async def deploy_on_remote_internal(self):
        # """Внутренняя логика удаленного деплоя"""
        # try:
        await self.log_message("🚀 Deploying on remote server...")

        secret = self.password.value if self.auth_method.value == "password" else self.ssh_key.value

        ssh_manager = SSHManager(
            host=self.host.value,
            user=self.username.value,
            secret=secret,
            port=int(self.port.value) if self.port.value else 22
        )

        ssh_manager.open_connection()

        if not ssh_manager.is_connection_opened():
            await self.log_message("❌ SSH connection failed")
            return False

        # Переходим в директорию проекта
        commands = [
            # "sudo -i",
            # "12356",
            "ls",
            f"cd {self.root}",
            "echo '=== Checking Docker installation ==='",
            "docker --version",
            "docker compose --version || docker compose version",
            "echo '=== Stopping existing containers ==='",
            "docker compose down || docker compose down",
            "echo '=== Building and starting containers ==='",
            "docker compose up --build -d || docker compose up --build -d",
            "echo '=== Checking container status ==='",
            "docker compose ps || docker compose ps",
            "echo '=== Deployment completed ==='"
        ]

        full_command = " && ".join(commands)

        await self.log_message("🔧 Executing deployment commands...")
        ssh_manager.execute_command(full_command, True)

        ssh_manager.close_connection()

        await self.log_message("✅ Remote deployment completed!")
        return True

    # except Exception as ex:
    #     await self.log_message(f"❌ Remote deployment error: {str(ex)}")
    #     return FalseS

    async def clone_repository(self):
        """Клонирует репозиторий"""
        if not self.git_url.value:
            await self.log_message("❌ Please enter Git repository URL")
            return False

        try:
            # Создаем временную директорию
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

            self.temp_dir = tempfile.mkdtemp()
            os.mkdir(os.path.join(self.temp_dir, "project"))
            self.current_project_path = os.path.join(self.temp_dir, "project")

            await self.log_message(f"📥 Cloning repository to {self.current_project_path}...")

            # Используем ваш GitManager
            git_manager = GitManager(
                git_url=self.git_url.value,
                repo_dir=self.current_project_path
            )

            git_manager.clone_repo()

            if os.path.exists(self.current_project_path) and len(os.listdir(self.current_project_path)) > 0:
                await self.log_message("✅ Repository cloned successfully!")
                return True
            else:
                await self.log_message("❌ Repository cloning failed")
                return False

        except Exception as ex:
            await self.log_message(f"❌ Clone error: {str(ex)}")
            return False


# Два варианта запуска:
def main():
    """Запуск приложения - выберите нужный вариант"""

    # Вариант 1: С дефолтным конфигом для тестов
    ft.app(target=AdvancedGitDeployerApp(use_default_config=True).main)

    # Вариант 2: Без дефолтного конфига (ручной ввод)
    # ft.app(target=AdvancedGitDeployerApp(use_default_config=False).main)


if __name__ == "__main__":
    main()
