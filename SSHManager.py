import paramiko

class SSHManager:
  def __init__(self, host, user, secret, port=22):
    self.host = host
    self.user = user
    self.secret = secret
    self.port = 22

    self.client = None

  def open_connection(self):
    self.client = paramiko.SSHClient()
    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
      self.client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
    except Exception as e:
      print(e)

  def is_connection_opened(self):
    if self.client == None:
      text = "Error: Connection is not opened. You can't close it"
      print("\033[31m{}".format(text))
      print("\u001b[0m")
      return False
    return True

  def close_connection(self):
    if self.is_connection_opened():
      self.client.close()

  def execute_command(self, command: str):
    if self.is_connection_opened:
      stdin, stdout, stderr = self.client.exec_command(command)

      print("\033[4mВывод команды:\u001b[0m")
      for line in iter(stdout.readline, ""):
        print(line, end="")


  def __del__(self):
    self.close_connection()
