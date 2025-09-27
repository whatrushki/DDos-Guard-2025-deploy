import os
import paramiko
from ConnectionManager import ConnectionManager


class SFTPManager(ConnectionManager):
    def __init__(self, host, user, secret, host_os: str, port=22):
        self.host_os = host_os
        super().__init__(host, user, secret, port=22)

    def open_connection(self):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(None, self.user, self.secret)
        try:
            self.client = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            print(e)

    def upload_files(self, from_dir, to_dir):

        if self.is_connection_opened():
            filenames = ["Dockerfile", "docker-compose.yml"]
            if self.host_os == "linux":
                slash = "/"
            else:
                slash = "\\"
            for filename in filenames:
                localpath = os.path.join(from_dir, filename)
                dst_dir = to_dir + slash + filename
                self.client.put(localpath, dst_dir)

    def _fix_permissions_and_upload(self, local_path, remote_path):
        """Пытается исправить права и загрузить файл"""
        try:
            # Пробуем изменить права на файл
            os.chmod(local_path, 0o644)
            self.client.put(local_path, remote_path)
            print(f"Uploaded (after permission fix): {local_path}")
        except Exception as e:
            print(f"Failed to upload {local_path}: {e}")