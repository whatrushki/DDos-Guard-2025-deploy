import flet as ft
import subprocess
import asyncio
import paramiko
from io import StringIO
import threading
import os


class GitDeployerApp:
    def __init__(self):
        self.page = None
        self.ssh_client = None

    async def main(self, page: ft.Page):
        self.page = page
        page.title = "Git Repository Deployer"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.scroll = ft.ScrollMode.ADAPTIVE

        # Элементы интерфейса
        self.git_url = ft.TextField(
            label="Git Repository URL",
            hint_text="https://github.com/username/repo.git",
            width=400
        )

        self.branch = ft.TextField(
            label="Branch (optional)",
            hint_text="main, develop, etc.",
            width=200
        )

        self.host = ft.TextField(
            label="Remote Host",
            hint_text="192.168.1.100 or domain.com",
            width=300
        )

        self.port = ft.TextField(
            label="SSH Port",
            value="22",
            width=100
        )

        self.username = ft.TextField(
            label="Username",
            hint_text="root, ubuntu, etc.",
            width=200
        )

        self.password = ft.TextField(
            label="Password/SSH Key",
            password=True,
            hint_text="Password or SSH private key",
            width=300
        )

        self.deploy_path = ft.TextField(
            label="Deploy Path on Remote",
            value="/var/www/app",
            width=300
        )

        self.log_output = ft.TextField(
            label="Log Output",
            multiline=True,
            min_lines=10,
            max_lines=15,
            read_only=True,
            width=600
        )

        self.progress_bar = ft.ProgressBar(
            width=600,
            visible=False
        )

        # Кнопки
        self.clone_btn = ft.ElevatedButton(
            "Clone Repository",
            icon=ft.icons.CLOUD_DOWNLOAD,
            on_click=self.clone_repository
        )

        self.deploy_btn = ft.ElevatedButton(
            "Deploy to Remote",
            icon=ft.icons.CLOUD_UPLOAD,
            on_click=self.deploy_to_remote
        )

        self.test_ssh_btn = ft.ElevatedButton(
            "Test SSH Connection",
            icon=ft.icons.LINK,
            on_click=self.test_ssh_connection
        )

        self.clear_log_btn = ft.ElevatedButton(
            "Clear Log",
            icon=ft.icons.CLEAR,
            on_click=self.clear_log
        )

        # Макет приложения
        await page.add_async(
            ft.Column([
                ft.Text("Git Repository Deployer", size=24, weight=ft.FontWeight.BOLD),

                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Git Repository Settings", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([self.git_url, self.branch]),
                        ]),
                        padding=15
                    )
                ),

                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Remote Server Settings", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([self.host, self.port]),
                            ft.Row([self.username, self.password]),
                            self.deploy_path,
                        ]),
                        padding=15
                    )
                ),

                ft.Row([
                    self.clone_btn,
                    self.deploy_btn,
                    self.test_ssh_btn,
                    self.clear_log_btn
                ]),

                self.progress_bar,
                self.log_output,
            ])
        )

    async def log_message(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_output.value += f"{message}\n"
        await self.log_output.update_async()
        await self.page.update_async()

    async def clear_log(self, e):
        """Очищает лог"""
        self.log_output.value = ""
        await self.log_output.update_async()

    async def set_loading(self, loading: bool):
        """Включает/выключает индикатор загрузки"""
        self.progress_bar.visible = loading
        self.clone_btn.disabled = loading
        self.deploy_btn.disabled = loading
        self.test_ssh_btn.disabled = loading
        await self.page.update_async()

    async def clone_repository(self, e):
        """Клонирует Git репозиторий"""
        if not self.git_url.value:
            await self.log_message("❌ Please enter Git repository URL")
            return

        await self.set_loading(True)
        await self.log_message("🔄 Cloning repository...")

        try:
            # Запускаем в отдельном потоке чтобы не блокировать UI
            threading.Thread(
                target=self._clone_repository_thread,
                daemon=True
            ).start()

        except Exception as ex:
            await self.log_message(f"❌ Error: {str(ex)}")
            await self.set_loading(False)

    def _clone_repository_thread(self):
        """Поток для клонирования репозитория"""
        asyncio.run(self._clone_repository_async())

    async def _clone_repository_async(self):
        """Асинхронное клонирование репозитория"""
        try:
            clone_cmd = ["git", "clone"]

            if self.branch.value:
                clone_cmd.extend(["-b", self.branch.value])

            clone_cmd.extend([self.git_url.value, "cloned_repository"])

            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                await self.log_message("✅ Repository cloned successfully!")

                # Показываем информацию о репозитории
                repo_info = await self.get_repository_info("cloned_repository")
                await self.log_message(f"📁 Repository info:\n{repo_info}")

            else:
                await self.log_message(f"❌ Clone failed: {stderr.decode()}")

        except Exception as ex:
            await self.log_message(f"❌ Clone error: {str(ex)}")

        finally:
            await self.set_loading(False)

    async def get_repository_info(self, repo_path: str) -> str:
        """Получает информацию о репозитории"""
        try:
            # Получаем текущую ветку
            branch_proc = await asyncio.create_subprocess_exec(
                "git", "-C", repo_path, "branch", "--show-current",
                stdout=asyncio.subprocess.PIPE
            )
            branch, _ = await branch_proc.communicate()

            # Получаем последний коммит
            commit_proc = await asyncio.create_subprocess_exec(
                "git", "-C", repo_path, "log", "-1", "--oneline",
                stdout=asyncio.subprocess.PIPE
            )
            commit, _ = await commit_proc.communicate()

            return f"Branch: {branch.decode().strip()}\nLast commit: {commit.decode().strip()}"

        except Exception as ex:
            return f"Error getting repo info: {str(ex)}"

    async def test_ssh_connection(self, e):
        """Тестирует SSH соединение"""
        if not all([self.host.value, self.username.value]):
            await self.log_message("❌ Please enter host and username")
            return

        await self.set_loading(True)
        await self.log_message("🔌 Testing SSH connection...")

        threading.Thread(
            target=self._test_ssh_thread,
            daemon=True
        ).start()

    def _test_ssh_thread(self):
        """Поток для тестирования SSH"""
        asyncio.run(self._test_ssh_async())

    async def _test_ssh_async(self):
        """Асинхронное тестирование SSH соединения"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_params = {
                'hostname': self.host.value,
                'username': self.username.value,
                'port': int(self.port.value) if self.port.value else 22,
            }

            # Определяем тип аутентификации
            if self.password.value and self.password.value.strip().startswith('-----BEGIN'):
                # SSH ключ
                private_key = paramiko.RSAKey.from_private_key(
                    StringIO(self.password.value)
                )
                connect_params['pkey'] = private_key
            else:
                # Пароль
                connect_params['password'] = self.password.value

            await self.log_message(f"🔗 Connecting to {self.host.value}...")
            ssh.connect(**connect_params, timeout=10)

            # Выполняем простую команду для проверки
            stdin, stdout, stderr = ssh.exec_command('uname -a')
            result = stdout.read().decode().strip()

            await self.log_message(f"✅ SSH connection successful!")
            await self.log_message(f"💻 System info: {result}")

            # Проверяем доступность пути деплоя
            stdin, stdout, stderr = ssh.exec_command(f'ls -la {self.deploy_path.value}')
            if stdout.channel.recv_exit_status() == 0:
                await self.log_message(f"✅ Deploy path exists: {self.deploy_path.value}")
            else:
                await self.log_message(f"⚠️ Deploy path doesn't exist (will be created)")

            ssh.close()

        except Exception as ex:
            await self.log_message(f"❌ SSH connection failed: {str(ex)}")

        finally:
            await self.set_loading(False)

    async def deploy_to_remote(self, e):
        """Деплоит репозиторий на удаленную машину"""
        if not all([self.git_url.value, self.host.value, self.username.value]):
            await self.log_message("❌ Please fill all required fields")
            return

        await self.set_loading(True)
        await self.log_message("🚀 Starting deployment...")

        threading.Thread(
            target=self._deploy_thread,
            daemon=True
        ).start()

    def _deploy_thread(self):
        """Поток для деплоя"""
        asyncio.run(self._deploy_async())

    async def _deploy_async(self):
        """Асинхронный деплой"""
        try:
            # 1. Клонируем репозиторий локально
            await self.log_message("📥 Cloning repository locally...")

            if os.path.exists("temp_deploy"):
                import shutil
                shutil.rmtree("temp_deploy")

            clone_cmd = ["git", "clone"]
            if self.branch.value:
                clone_cmd.extend(["-b", self.branch.value])
            clone_cmd.extend([self.git_url.value, "temp_deploy"])

            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

            if process.returncode != 0:
                await self.log_message("❌ Failed to clone repository")
                return

            # 2. Подключаемся по SSH
            await self.log_message("🔗 Connecting to remote server...")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_params = {
                'hostname': self.host.value,
                'username': self.username.value,
                'port': int(self.port.value) if self.port.value else 22,
            }

            if self.password.value and self.password.value.strip().startswith('-----BEGIN'):
                private_key = paramiko.RSAKey.from_private_key(StringIO(self.password.value))
                connect_params['pkey'] = private_key
            else:
                connect_params['password'] = self.password.value

            ssh.connect(**connect_params, timeout=30)

            # 3. Создаем директорию на удаленной машине
            await self.log_message("📁 Creating deployment directory...")
            ssh.exec_command(f'mkdir -p {self.deploy_path.value}')

            # 4. Копируем файлы через SFTP
            await self.log_message("📤 Uploading files...")
            sftp = ssh.open_sftp()

            def upload_directory(local_path, remote_path):
                for item in os.listdir(local_path):
                    local_item = os.path.join(local_path, item)
                    remote_item = remote_path + '/' + item

                    if os.path.isfile(local_item):
                        sftp.put(local_item, remote_item)
                    else:
                        try:
                            sftp.mkdir(remote_item)
                        except:
                            pass
                        upload_directory(local_item, remote_item)

            upload_directory("temp_deploy", self.deploy_path.value)
            sftp.close()

            # 5. Опционально: запускаем установку зависимостей
            await self.log_message("🔧 Checking for package.json...")
            if os.path.exists("temp_deploy/package.json"):
                await self.log_message("📦 Found package.json, installing dependencies...")
                ssh.exec_command(f'cd {self.deploy_path.value} && npm install --production')

            # 6. Очистка
            import shutil
            shutil.rmtree("temp_deploy")
            ssh.close()

            await self.log_message("✅ Deployment completed successfully!")

        except Exception as ex:
            await self.log_message(f"❌ Deployment failed: {str(ex)}")

        finally:
            await self.set_loading(False)


# Запуск приложения
if __name__ == "__main__":
    ft.app(target=GitDeployerApp().main)