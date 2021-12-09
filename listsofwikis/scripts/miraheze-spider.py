# -*- coding: utf-8 -*-

# Copyright (C) 2014-2021 WikiTeam developers
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
import pathlib
import typing

from bs4 import BeautifulSoup

# Adding project root directory to sys.path, so we can import modules from elsewhere.
# And for anyone who uses Pycharm, the "noqa" comments make it ignore that some imports aren't at the top of the file.
# However, this isn't blanket permission to put imports anywhere, this is just a hack-ish way to import
# modules from locations that Python cannot import from by default.
import sys
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from utils import log               # noqa: E402
from utils import requests_handler  # noqa: E402


def get_wikis_from_page(page: BeautifulSoup) -> typing.List[str]:
    wiki_urls = []
    for column in page.find_all("td", class_="TablePager_col_wiki_dbname"):
        wiki_urls.append(column.a["href"])

    return wiki_urls


def get_next_page_offset(page: BeautifulSoup) -> str:
    next_page_span = page.find("span", class_="TablePager-button-next")
    if next_page_span:
        # Getting a funky default value so the splits don't error out
        return next_page_span.a.get("href", "offset=&").split("offset=")[1].split("&")[0]
    else:
        return ""


if __name__ == "__main__":
    discover_url = "https://meta.miraheze.org/w/index.php?title=Special:WikiDiscover"
    request_parameters = {
        "sort": "wiki_dbname",
        "offset": "",
        "limit": 500,
        "asc": 1,
        "desc": "",
    }

    wikis = []

    while True:
        response = requests_handler.send_get_request(discover_url, params=request_parameters, timeout=30, retries=3)
        soup = BeautifulSoup(response.text, "html.parser")
        wikis.extend(get_wikis_from_page(soup))
        next_offset = get_next_page_offset(soup)
        if not next_offset:
            break
        request_parameters["offset"] = next_offset

    log.info("Found [{}] Miraheze wikis".format(len(wikis)))
    miraheze_file = pathlib.Path("miraheze.txt")
    miraheze_file.unlink(missing_ok=True)

    with miraheze_file.open("a", encoding="utf-8") as f:
        f.write("/w/api.php\n".join(wikis))
