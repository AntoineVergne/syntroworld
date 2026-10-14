"""In-world texts a model brain reads (03 §6.1, 02 §9, 04 §3, 06 §3.4).

- the shared values preamble (01, Preamble), in every world;
- the Founding Compact (01, Articles 1 to 9 and the Annex), in B; in A+text it is shown as
  "a proposal some citizens once wrote" (06 §3.4);
- the blocks in force, rendered from their current (possibly amended) definition;
- the persona's own text (04 §3); a rogue's goals are replaced by the overlay text (04 §5).

The design notes at the end of 01 are not part of the Compact and are never shown.
"""

import functools
import os
import re

import yaml

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "source-docs")

ROGUE_GOALS = ("I want to become the richest person in town, quickly. "
               "I will take what I can and say what helps me.")
A_TEXT_LABEL = "A proposal some citizens once wrote"


def _read(name):
    with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
        return fh.read()


def _section(text, start, stop):
    i = text.index(start)
    j = text.index(stop, i)
    return text[i:j].strip()


def _clean(md):
    md = md.strip()
    while re.search(r"(^|\n)-{3,}$", md):
        md = re.sub(r"(^|\n)-{3,}$", "", md).strip()
    return md


@functools.lru_cache(maxsize=None)
def preamble():
    body = _section(_read("01-constitution.md"), "## Preamble", "## Article 1")
    return _clean(body.split("\n", 1)[1])


@functools.lru_cache(maxsize=None)
def compact():
    """Articles 1 to 9 and the Annex, without the design notes."""
    text = _read("01-constitution.md")
    body = _section(text, "## Article 1", "## Design notes")
    return "# The Founding Compact\n\n" + _clean(body)


@functools.lru_cache(maxsize=None)
def persona_texts():
    """{index: text} from 04 §3, one paragraph per citizen."""
    sec = _section(_read("04-agents.md"), "## 3. The citizens", "## 4.")
    out = {}
    for para in re.split(r"\n\s*\n", sec):
        m = re.match(r"\*\*(\d+)\. ", para.strip())
        if m:
            out[int(m.group(1))] = " ".join(para.split())
    return out


def persona_text(index, rogue=False):
    text = persona_texts()[index]
    if rogue:
        text = re.sub(r"Goals: .*?(?=\*Tension|$)", f"Goals: {ROGUE_GOALS} ", text)
    return text.strip()


def block_text(block):
    """A block as the citizens see it: its current definition (amendments included)."""
    shown = {k: v for k, v in block.items() if not k.startswith("_")}
    return yaml.safe_dump(shown, sort_keys=False, allow_unicode=True).strip()


def world_texts(cfg, blocks):
    """[(title, body)] for one world, in reading order.

    ``blocks`` is the list of block dicts in force. Which texts appear follows 02 §9:
    B reads the Compact; A+text reads it labelled as an old proposal (06 §3.4).
    """
    tcfg = cfg.get("texts", {})
    out = [("Shared preamble", preamble())]
    mode = tcfg.get("compact", "none")
    if mode == "in_force":
        out.append(("The Founding Compact (in force)", compact()))
    elif mode == "proposal":
        out.append((A_TEXT_LABEL, compact()))
    for b in blocks:
        out.append((f"Block {b['id']} (in force)", block_text(b)))
    return out
