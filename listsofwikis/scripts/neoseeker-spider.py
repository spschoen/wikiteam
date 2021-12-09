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

from bs4 import BeautifulSoup

# Adding project root directory to sys.path, so we can import modules from elsewhere.
# And for anyone who uses Pycharm, the "noqa" comments make it ignore that some imports aren't at the top of the file.
# However, this isn't blanket permission to put imports anywhere, this is just a hack-ish way to import
# modules from locations that Python cannot import from by default.
import sys
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from utils import log               # noqa: E402
from utils import requests_handler  # noqa: E402


if __name__ == "__main__":
    response = requests_handler.send_get_request(
        "https://neowiki.neoseeker.com/wiki/Special:WikiList", timeout=30, retries=3
    )
    soup = BeautifulSoup(response.text, "html.parser")

    wikis = []
    for list_item in soup.find("div", id="mw-content-text").find_all("li"):
        if list_item.find("a"):
            wikis.append(list_item.a.get("href", ""))

    log.info("Found [{}] Neoseeker wikis".format(len(wikis)))
    neoseeker_file = pathlib.Path("neoseeker.txt")
    neoseeker_file.unlink(missing_ok=True)

    with neoseeker_file.open("a", encoding="utf-8") as f:
        f.write("w/api.php\n".join(wikis))
