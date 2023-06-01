import logging


def logger(name, mode: str = "a"):
    logger_ = logging.getLogger(name)
    logger_.setLevel(logging.ERROR)

    handler_file = logging.FileHandler(f"logs/{name}.log", mode=mode)
    handler_console = logging.StreamHandler()

    formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
    handler_file.setFormatter(formatter)
    handler_console.setFormatter(formatter)

    logger_.addHandler(handler_file)
    logger_.addHandler(handler_console)
    return logger_
