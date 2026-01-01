import logging

def setup_logging(log_file: str = "sketch_v4.log"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()   # also print to console
        ]
    )
    logging.info("Logging initialized. Writing to %s and console.", log_file)