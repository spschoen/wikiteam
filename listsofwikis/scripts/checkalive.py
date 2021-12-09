# -*- coding: utf-8 -*-

# Copyright (C) 2011-2012 WikiTeam
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Script to check if a list of wikis are alive or dead

import concurrent.futures
import pathlib
import requests
import typing

# Adding project root directory to sys.path, so we can import modules from elsewhere.
# And for anyone who uses Pycharm, the "noqa" comments make it ignore that some imports aren't at the top of the file.
# However, this isn't blanket permission to put imports anywhere, this is just a hack-ish way to import
# modules from locations that Python cannot import from by default.
import sys
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from utils import log          # noqa: E402

from wikiteam import wikiteam  # noqa: E402


# Configuration
delay = 30               # Seconds before timing out on request
check_batch_limit = 100  # How many URLs to check at once


def wiki_is_alive(wiki_url: str) -> bool:
    try:
        response = requests.get(wiki_url, timeout=60)
    except Exception as e:
        log.error("URL [{}] returned error: [{}]".format(wiki_url, str(e)))
        return False

    if 300 <= response.status_code < 400 or response.status_code == 404:
        return False

    try:
        return wikiteam.get_wiki_engine_from_response(response) != "Unknown"
    except RuntimeError as rte:
        if "blocked by Captcha" in str(rte):
            return False
        raise rte


def check(urls: typing.List[str]) -> typing.List[typing.List[typing.Union[str, bool]]]:
    wikis_and_statuses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
        future_to_url = {executor.submit(wiki_is_alive, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            is_alive = future.result()
            wikis_and_statuses.append([url, is_alive])

    return wikis_and_statuses


if __name__ == "__main__":
    wiki_file = pathlib.Path("urls_to_check.txt")
    alive_file = pathlib.Path("wikis_alive.txt")
    dead_file = pathlib.Path("wikis_dead.txt")

    if not wiki_file.exists():
        raise ValueError("Could not find {}; cannot check for wikis".format(wiki_file.name))

    alive_file.unlink(missing_ok=True)
    dead_file.unlink(missing_ok=True)

    urls_to_check = [x.strip() for x in wiki_file.read_text(encoding="utf-8").splitlines(keepends=False)]

    log.info("Checking [{}] urls".format(len(urls_to_check)))

    for x in range(0, len(urls_to_check), check_batch_limit):
        log.info("Scanning URLs from index [{}] to [{}]".format(x, x + check_batch_limit))
        wiki_statuses = check(urls_to_check[x:x + check_batch_limit])
        alive_wikis = [x for x in wiki_statuses if x[1]]
        dead_wikis = [x for x in wiki_statuses if not x[1]]
        log.debug("Found [{}] alive wikis and [{}] dead ones".format(len(alive_wikis), len(dead_wikis)))

        if alive_wikis:
            with alive_file.open("a", encoding="utf-8") as f:
                f.write("\n".join([x[0] for x in alive_wikis]))
                f.write("\n")

        if dead_wikis:
            with dead_file.open("a", encoding="utf-8") as f:
                f.write("\n".join([x[0] for x in dead_wikis]))
                f.write("\n")

    if alive_file.exists():
        final_alive_talley = len([x for x in alive_file.read_text(encoding="utf-8").splitlines(keepends=False) if x])
    else:
        final_alive_talley = 0

    if dead_file.exists():
        final_dead_talley = len([x for x in dead_file.read_text(encoding="utf-8").splitlines(keepends=False) if x])
    else:
        final_dead_talley = 0

    log.info(
        "[{}] URLs out of [{}] worked; [{}] didn't".format(final_alive_talley, len(urls_to_check), final_dead_talley)
    )
