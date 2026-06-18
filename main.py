import os
import subprocess
import sys

# Kutubxonalarni kod ishga tushayotganda yuklaymiz
def install_dependencies():
    packages = ["aiogram", "osmnx", "networkx", "pandas"]
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

# Qolgan kodni shu yerdan pastga joylashtiring...
import asyncio
import logging
# ... (qolgan barcha kodlaringiz shu yerdan pastda tursin)