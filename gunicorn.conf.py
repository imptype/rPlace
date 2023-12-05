import multiprocessing

worker_class = 'uvicorn.workers.UvicornWorker'
workers = multiprocessing.cpu_count()