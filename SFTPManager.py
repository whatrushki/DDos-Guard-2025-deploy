import os

import paramiko

from ConnectionManager import ConnectionManager

class SFTPManager(ConnectionManager):
  def __init__(self, host, user, secret, port=22):
    super().__init__(host, user, secret, port=22)

  def open_connection(self):
    tranport = paramiko.Transport((self.host, self.port))
    tranport.connect(None, self.user, self.secret)
    try:
      self.client = paramiko.SFTPClient.from_transport(tranport)
    except Exception as e:
      print(e)

  def upload_files(self, dir_path):
    if self.is_connection_opened():
      generated_files_path = os.path.join(".", "generated_files")
      filenames = os.listdir(generated_files_path)
      for filename in filenames:
        localpath = os.path.join(generated_files_path, filename)

        print(localpath)

        self.client.put(localpath, os.path.join(dir_path, filename))
