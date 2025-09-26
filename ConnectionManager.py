class ConnectionManager:
  def __init__(self, host, user, secret, port=22):
    self.host = host
    self.user = user
    self.secret = secret
    self.port = 22

    self.client = None

  def open_connection(self):
    pass

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

  def __del__(self):
    self.close_connection()
