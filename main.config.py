wsgi_app = "main:app"
with open(".env", "r") as file:
    env = file.read().splitlines()

bind = "localhost:8080"
worker_class = "uvicorn.workers.UvicornWorker"
reload = True
