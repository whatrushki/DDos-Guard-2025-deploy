# from GitManager import GitManager
# from SSHManager import SSHManager
# from SFTPManager import SFTPManager
#
# import os
#
# git_url = "https://github.com/NekrasovVM/Bitrix.git"
# repo_dir = "/media/nekra/Acer/Ubuntu/test_dir_local"
#
# remote_repo_dir = "/media/nekra/Acer/Ubuntu/test_dir"
#
# print("Cloning repo to local machine")
# git_manager = GitManager(git_url, repo_dir)
# git_manager.clone_repo()
#
# print("Analyzing...")
# print("Code generating...")
#
# print("Creating remote repo...")
# ssh_manager = SSHManager("127.0.0.1", "nekra", "251339795")
# ssh_manager.open_connection()
# ssh_manager.execute_command(f"""ls -l
#                             cd {remote_repo_dir}
#                             git clone {git_url}
#                             """)
#
# sftp_manager = SFTPManager("127.0.0.1", "nekra", "251339795")
# sftp_manager.open_connection()
# sftp_manager.upload_files(os.path.join(remote_repo_dir, git_url.split('/')[-1].replace(".git", "")))
#
# ssh_manager.close_connection()
# sftp_manager.close_connection()
