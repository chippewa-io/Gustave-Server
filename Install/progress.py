import apt
import apt.progress
import os
import time
import sys

# Define the progress file path at the start of the script
progress_file = "/tmp/install_progress.txt"
class InstallProgress(apt.progress.base.InstallProgress):
    def __init__(self):
        super().__init__()
        self.processed_packages = 0

    def start_update(self):
        super().start_update()
        self.write_to_file("Installation has started.")

    def status_change(self, pkg, percent, status):
        super().status_change(pkg, percent, status)
        self.processed_packages += 1
        self.write_to_file(f"Package: {pkg} - Status: {status}, Percent: {percent}")

    def error(self, pkg, errormsg):
        super().error(pkg, errormsg)
        self.write_to_file(f"An error occurred: {errormsg}")

    def finish_update(self):
        super().finish_update()
        self.write_to_file("Installation finished, Percent: 100")

    def write_to_file(self, message):
        #print(message)  # Print to console
        with open(progress_file, "a") as f:
            f.write(message + "\n")  # Append to file

# Redirect stdout
devnull = open(os.devnull, 'w')
old_stdout = sys.stdout
sys.stdout = devnull

cache = apt.Cache()
cache.update()
cache.open(None)
cache["mysql-server"].mark_install()

progress = InstallProgress()
cache.commit(install_progress=progress)

# Restore stdout
sys.stdout = old_stdout
devnull.close()