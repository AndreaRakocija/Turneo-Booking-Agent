import logging

uvicorn_loggers = ["uvicorn", "uvicorn.error", "uvicorn.access"]
for name in uvicorn_loggers:
    logging.getLogger(name).handlers.clear()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
