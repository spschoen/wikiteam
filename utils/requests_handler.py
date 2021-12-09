import requests
import time
import typing

from utils import log


def get_user_agent() -> str:
    """
    Return a user-agent to hide Python default user-agent

    # TODO: Method to do user-agent _and_ other headers

    :return: fake user agent
    """
    user_agents = [
        # firefox
        "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    ]
    return user_agents[int(time.time()) % 2]


def get_or_set_session(session: typing.Optional[requests.sessions.Session] = None) -> requests.sessions.Session:
    """
    Check if user supplied a session, and if not, create one.  Adds a generic(ish) user agent header to the session
    if not already present.

    :param session: session key word argument passed to sent_get_request or send_post_request
    :return: session object (newly created, or passed from higher function)
    """
    # Removing the session object from the data we send
    if not session:
        session = requests.Session()

    if session.headers.get("User-Agent", None):
        session.headers.update({"User-Agent": get_user_agent()})

    return session


def handle_status_code(response: requests.Response) -> None:
    """
    Check the return code of a request, and either error on 404/429/5XX, print a debug message on 3XX/401/403, or
    do nothing for 2XX.

    :param response: object returned by requests.get()
    :return: None
    """
    status_code = response.status_code
    if 200 <= status_code < 300:
        return

    log.warning("Request [{}] got HTTP Code [{}]".format(response.url, status_code))
    if 300 <= status_code < 400:
        log.warning("Redirect should happen automatically: please report this as a bug.")
        log.debug(response.url)

    elif status_code == 400:
        log.error("Bad Request to [{}]: The wiki may be malfunctioning; please try again later.".format(response.url))
        raise RuntimeError("Got error code 400 from wiki")

    elif status_code == 401 or status_code == 403:
        log.error("Authentication required; please use --user and --pass.")
        raise RuntimeError("Need to be authenticated to archive this wiki")

    elif status_code == 404:
        raise RuntimeError("Got error code 404 on request to [{}]".format(response.url))

    elif status_code == 429 or (500 <= status_code < 600):
        log.error("Max retries exceeded when accessing [{}]; please resume the dump later.".format(response.url))
        raise RuntimeError("Max retries exceeded")


def send_get_request(url: str, **kwargs) -> requests.Response:
    """
    Send a GET request to a URL with arbitrary parameter dict kwargs, return the response with proper encoding if the
    Byte Order Mark is present.

    :param url: URL to GET
    :param kwargs: arbitrary parameters to send with the request
    :return: Response from URL, with encoding set properly if necessary.
    """

    # If defined, keep from sending requests too often.
    delay = kwargs.pop("delay", 0)

    # If defined, retry the request X times until successful (and make sure it runs at least once!)
    retries = max(kwargs.pop("retries", 1), 1)

    session = get_or_set_session(kwargs.pop("session", None))

    for x in range(retries):
        try:
            time.sleep(delay)
            response = session.get(url, **kwargs)

            # Checking for the Byte Order Mark (BOM), which we need to change encoding to properly handle later on
            if response.text.startswith("\ufeff"):
                response.encoding = "utf-8-sig"

            handle_status_code(response)
            return response
        except Exception as e:
            log.error("Received error for GET request: [{}]".format(str(e)))
    else:
        raise RuntimeError("Exceeded retries when trying to retrieve [{}]".format(url))


def send_post_request(url: str, **kwargs) -> requests.Response:
    """
    Send a POST request to a URL with arbitrary parameter dict kwargs, return the response with proper encoding if the
    Byte Order Mark is present.

    :param url: URL to POST
    :param kwargs: arbitrary parameters to send with the request
    :return: Response from URL, with encoding set properly if necessary.
    """

    # If defined, keep from sending requests too often.
    time.sleep(kwargs.pop("delay", 0))

    session = get_or_set_session(kwargs.pop("session", None))
    response = session.post(url, **kwargs)

    # Checking for the Byte Order Mark (BOM), which we need to change encoding to properly handle later on
    if response.text.startswith("\ufeff"):
        response.encoding = "utf-8-sig"

    handle_status_code(response)

    return response
