import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
timeout = 60

# Project paths
chdir = os.path.dirname(os.path.abspath(__file__))
pythonpath = os.path.join(chdir, "backend/chatbot_dir")

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
