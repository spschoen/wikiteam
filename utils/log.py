import json
import logging.config
import pathlib
import typing


# Stack level 0 displays the information of the log message function
# Stack level 1 displays the information of the log message function
# Stack level 2 displays the information of the function that called the log message function
# Stack level 3 displays the information of the function that called the function that called the log message function
# [repeat "the function that called" as stack level increases]
STACK_LEVEL_CURRENT_FUNCTION = 1
STACK_LEVEL_DEFAULT = 2
STACK_LEVEL_PREVIOUS = 3
STACK_LEVEL_PREVIOUS_PREVIOUS = 4

# We don't care for other logger debug output, if we need that info it's because we're passing bad info to the module.
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("chardet").setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.INFO)


logging_config_file = pathlib.Path(__file__).parent.parent.joinpath("configs", "logging.json")
logging_config = json.loads(logging_config_file.read_text())
logging.config.dictConfig(logging_config)
dump_generator_logger = logging.getLogger("dump_generator_logger")

original_handlers = dump_generator_logger.handlers.copy()  # explanation in setup_dump_errors_file()


def debug(message: typing.Any, stack_level: int = STACK_LEVEL_DEFAULT) -> None:
    dump_generator_logger.debug(str(message), stacklevel=stack_level)


def info(message: typing.Any, stack_level: int = STACK_LEVEL_DEFAULT) -> None:
    dump_generator_logger.info(str(message), stacklevel=stack_level)


def warning(message: typing.Any, stack_level: int = STACK_LEVEL_DEFAULT) -> None:
    dump_generator_logger.warning(str(message), stacklevel=stack_level)


def error(message: typing.Any, stack_level: int = STACK_LEVEL_DEFAULT) -> None:
    dump_generator_logger.error(str(message), stacklevel=stack_level)


def critical(message: typing.Any, stack_level: int = STACK_LEVEL_DEFAULT) -> None:
    dump_generator_logger.critical(str(message), stacklevel=stack_level)


def setup_dump_errors_file(dump_path: pathlib.Path) -> None:
    """
    Setup the logger to automatically write errors to <dump path>/errors.txt

    :param dump_path: path to wiki dump
    :return: None
    """
    dump_path.mkdir(parents=True, exist_ok=True)
    file_logger = logging.FileHandler(dump_path.joinpath("errors.txt"))
    file_logger.setLevel(logging.ERROR)
    formatter = logging.Formatter(logging_config["formatters"]["errors"]["format"], "%Y-%m-%d %H:%M:%S")
    file_logger.setFormatter(formatter)

    # This is in case someone runs dumpgenerator.py multiple times from the same script, just resetting the
    # handlers to the ones defined in the file at runtime start.
    # Without it, the logger will write to the first and second <dump path>/errors.txt files, instead of the second.
    # (This is really unlikely to happen as I imagine most people would just run dumpgenerator.py <args>
    #  but just in case (AKA in my testing), we should still handle this event)
    for handler in dump_generator_logger.handlers:
        dump_generator_logger.removeHandler(handler)
    for handler in original_handlers:
        dump_generator_logger.addHandler(handler)

    dump_generator_logger.addHandler(file_logger)
