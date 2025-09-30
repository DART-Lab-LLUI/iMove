from loguru import logger
import multiprocessing

# logger.add("debug.log", enqueue=True, level="DEBUG")
multiprocessing.set_start_method("spawn", force=True)

if __name__ == "__main__":
    from . import imove_app
    imove_app.main()
