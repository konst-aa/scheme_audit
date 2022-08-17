from typing import Tuple
from venv import create
from bs4 import BeautifulSoup as bs
from urllib.request import Request, urlopen
import json
import ssl

# no messing with state
def fast_soup(url: str) -> bs:
    context = ssl.SSLContext()
    req = Request(url, headers={"User-Agent": "Magic Browser"})
    return bs(urlopen(req, context=context))


# side effects galore
def dump_html_as_txt(url: str) -> str:
    with open("../manual-plaintexts/gambit-scheme.txt", "w", encoding="utf-8") as f:
        f.write(str(fast_soup(url)))


# dump_html_as_txt("https://gambitscheme.org/latest/manual/")


def definition_from_string(def_str: str) -> Tuple:
    # i am NOT going to use reduce, and I completely trust
    # that fn definitions will lack parentheses... right?? :)

    temp = def_str.split(")")
    t = temp[-1]
    tokens = temp[0].split(" ")
    definition = {
        "name": tokens[0][1:],
        "arity": 0,
        "args": [],
    }
    squares = 0
    named = False
    for token in tokens[1:]:
        temp = {}
        if token.startswith("["):
            squares += token.count("[")  # assuming all at are beginning, too tired

        if squares > 0:
            if token.endswith(":"):
                named = True
                continue
            temp = {
                "name": token.split("]")[0].split("[")[0],
                "optional?": True,
                "named?": named,
            }
            named = False
        else:
            if token.endswith("…"):
                definition["arity"] = "infinite"
                definition["args"] += [
                    {"name": token, "optional?": True, "named?": False}
                ]
                break
            temp = {"name": token, "optional?": False, "named?": False}
        definition["arity"] += 1
        definition["args"] += [temp]

        if token.endswith("]"):
            squares -= token.count("]")
    return (t, definition)


with open("../manual-plaintexts/gambit-scheme.txt", "r", encoding="utf-8") as f:
    soup = bs(f.read())
    table_rows = soup.find_all(
        "tr",
    )
    # seems fast enough
    code_items = [
        item
        for item in table_rows
        if item.find_all(lambda tag: tag.get("align") == "left")
        and item.find_all("code")
        and "(" in item.text
    ]

    # problems - no way to extract documentation, but will be useful to extract info regardless
    info_rows = [row.text[1:] for row in code_items]
    really_large_dict = {
        "special form": [],
        "procedure": [],
        "undefined": [],
        "variable": [],
    }
    for row in code_items:
        (t, definition) = definition_from_string(row.text[1:])
        really_large_dict[t] += [definition]

    with open("../jsons/gambit-scheme-definitions.json", "w", encoding="utf-8") as gs:
        gs.seek(0)
        gs.truncate()
        gs.write(json.dumps(really_large_dict, indent=4))

    print(f"{len(really_large_dict['procedure'])} procedures")
    print(f"{len(really_large_dict['special form'])} special forms")
