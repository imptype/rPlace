import multiprocessing

worker_class = 'uvicorn.workers.UvicornWorker'
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 20
loglevel = 'warning'