import os

from git import Repo

class GitManager:
  def __init__(self, git_url, repo_dir):
    self.git_url = git_url
    self.repo_dir = repo_dir

  def clone_repo(self):
    if len(os.listdir(self.repo_dir)) != 0:
      text = "Error: Target directory is not empty. Cloning interrupted"
      print("\033[31m{}".format(text))
      return

    try:
      Repo.clone_from(self.git_url, self.repo_dir)
    except Exception as e: 
      print(e)
    else:
      print("Repo cloned successfully!")
