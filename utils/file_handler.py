import hashlib

from utils import log


def truncate_filename(filename: str, filename_limit: int = 100) -> str:
    """
    Truncate filenames when downloading images with large filenames

    :param filename: string to truncate
    :param filename_limit: max length of filename, truncate after that length
    :return: filename, truncated if over filename_limit
    """

    if len(filename) > filename_limit:
        filename_hash = hashlib.md5(filename.encode("utf-8")).hexdigest() + "." + filename.split(".")[-1]
        filename = filename[:filename_limit] + filename_hash
        log.debug("Filename is too long, truncating to [{}]".format(filename))

    return filename


def get_windows_safe_filename(original_filename: str) -> str:
    """
    Removes the following characters: <>:"/\\|?*

    :param original_filename: possible unsafe string for a file
    :return: safe string for file
    """
    invalid_characters = "<>:\"/\\|?*"
    filename = original_filename.replace("\"", "'").replace(":", "-")
    return "".join(c for c in filename if c not in invalid_characters)
