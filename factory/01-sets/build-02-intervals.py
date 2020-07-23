#! /usr/bin/env python3

import re

from collections import defaultdict
from itertools import product

from mistool.os_use import PPath
from mistool.string_use import between, joinand
from orpyste.data import ReadBlock

BASENAME = PPath(__file__).stem.replace("build-", "")
BASENAME = BASENAME.replace("[slow]", "")

THIS_DIR = PPath(__file__).parent
STY_FILE = THIS_DIR / f'{BASENAME}.sty'
TEX_FILE = STY_FILE.parent / (STY_FILE.stem + "[fr].tex")

PATTERN_FOR_PEUF = re.compile("\d+-(.*)")
match            = re.search(PATTERN_FOR_PEUF, STY_FILE.stem)
PEUF_FILE        = STY_FILE.parent / (match.group(1).strip() + ".peuf")

DECO = " "*4


# ----------- #
# -- TOOLS -- #
# ----------- #

DELIMS = {
    '[...]': "C",
    ']...[': "O"
}

def latexid(delimID, subconfig):
    if delimID == "O":
        delimID = subconfig.get("O", delimID)

    return delimID

def parse(subconfig):
    global DELIMS

    ready2use = defaultdict(list)

    presuffs_used = []

    for interkind, defs in subconfig.items():
        delims = {
            kind: [x.strip() for x in defs[configkey].split('...')]
            for configkey, kind in DELIMS.items()
        }

        for left, right in product("CO", "OC"):
            delimstart, delimend =  delims[left][0], delims[right][1]

            left  = latexid(left, subconfig[interkind])
            right = latexid(right, subconfig[interkind])

            prefix = subconfig[interkind].get("prefix", "")

            suffix = left

            if left != right:
                suffix += right

            if (prefix, suffix) not in presuffs_used:
                presuffs_used.append((prefix, suffix))


                ready2use[interkind].append(
                    (prefix, suffix, delimstart, delimend)
                )

    return ready2use

def texmacro(prefix, suffix, delimstart, delimend):
    macroname = f"{prefix}interval{suffix}"

    return f"""
\\newcommand\\{macroname}{{\\@ifstar{{\\tnssets@{macroname}@star}}{{\\tnssets@{macroname}@no@star}}}}
\\newcommand\\tnssets@{macroname}@no@star[2]{{\\ensuremath{{\\tns@generic@interval@ext{{{delimstart}}}{{#1}}{{\\tnsmathsep}}{{#2}}{{{delimend}}}}}}}
\\newcommand\\tnssets@{macroname}@star[2]{{\\ensuremath{{\\tns@generic@interval@semi@ext{{{delimstart}}}{{#1}}{{\\tnsmathsep}}{{#2}}{{{delimend}}}}}}}
    """.strip() + "\n"

def texdoc(prefix, suffix):
    macroname = f"{prefix}interval{suffix}"

    return f"""
\\IDmacro*[1]{{{macroname}}}{{2}}

\\IDmacro*   {{{macroname}*}}{{2}}

\\IDarg{{1}} borne inférieure $a$ de l'intervalle $\\{macroname}{{a}}{{b}}$.

\\IDarg{{2}} borne supérieure $b$ de l'intervalle $\\{macroname}{{a}}{{b}}$.
    """.strip() + "\n"


# ------------ #
# -- CONFIG -- #
# ------------ #

with open(
    file     = TEX_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as docfile:
    template_tex = docfile.read()


with open(
    file     = STY_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as styfile:
    template_sty = styfile.read()


with ReadBlock(
    content = PEUF_FILE,
    mode    = "k::="
) as data:
    config = parse(data.mydict("std mini"))

for interkind, defs in config.items():
    fortexdoc  = []
    macrosdefs = []

    for prefix, suffix, delimstart, delimend in defs:
        macrosdefs += [
            "\n",
            texmacro(prefix, suffix, delimstart, delimend)
        ]

        fortexdoc += [
            "\n\n\\separation\n\n",
            "\n",
            texdoc(prefix, suffix)
        ]

    fortexdoc  = "".join(fortexdoc[1:])
    macrosdefs = "".join(macrosdefs)

    interkind = interkind.replace('-', ' ')

    text_start, _, text_end = between(
        text = template_sty,
        seps = [
            f"% Macros for {interkind} intervals",
            "% Macros for"
        ],
        keepseps = True
    )

    template_sty = text_start + "\n" + macrosdefs \
                 + "\n" + text_end

    text_start, _, text_end = between(
        text = template_tex,
        seps = [
            f"% Docs for {interkind} intervals - START",
            f"% Docs for {interkind} intervals - END",
        ],
        keepseps = True
    )

    template_tex = text_start + "\n" + fortexdoc \
                 + "\n" + text_end


# -------------------------- #
# -- UPDATES OF THE FILES -- #
# -------------------------- #

with open(
    file     = TEX_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(template_tex)

with open(
    file     = STY_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(template_sty)
