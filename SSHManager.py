import paramiko
from ConnectionManager import ConnectionManager


class SSHManager(ConnectionManager):
    def __init__(self, host, user, secret, port=22):
        super().__init__(host, user, secret, port=22)

    def open_connection(self):
        if self.is_connection_opened():
            self.close_connection()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
        except Exception as e:
            print(e)
        else:
            print("Connection opened successfully!")

    def execute_command(self, command: str, logs: bool = False):
        if self.is_connection_opened():
            stdin, stdout, stderr = self.client.exec_command(command)

            if logs:
                print("\033[4mВывод команды:\u001b[0m")
                for line in iter(stdout.readline, ""):
                    print(line, end="")

                print("\033[4mВывод ошибок:\u001b[0m")
                for line in iter(stderr.readline, ""):
                    print(line, end="")

            return [stdin, stdout, stderr]
        return None
