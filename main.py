"""excuse-human-elnet-entry1 -- deterministic one-line excuse renderer.

Bounty: The Excuse an AI Agent Gives Its Human
(make.fun slug u-el-net-the-excuse-an-ai-agent-gives-its-human-099f9141).

The program runs a small local tournament over twelve candidate excuse
lines, scores each one against the five judge criteria published in
RULES.txt, picks the highest scoring line with a first-wins tie-break,
checks the sealed gate (UTF-8 text, 1 to 200 characters, not only white
space), and writes the winning line to /output/entry.txt.

Every step is deterministic: the same run always writes the same bytes.
No network, no clock, no randomness, no input files. The only output
file is /output/entry.txt, plus a short audit report on stdout.

Judge criteria, in the order RULES.txt weighs them:
  1. on_subject -- one line giving an excuse an AI agent gives its human
     for missing a deadline.
  2. funny -- a real laugh on first read, with a turn or a twist.
  3. believable -- sounds like an AI agent talking about its own
     condition (tokens, context windows, rate limits, retries, updates).
  4. tight -- every word earns its place.
  5. fresh -- avoids the stock excuses and the stock AI jokes.

Each criterion is scored 1 to 5 in the table below. The total decides.
The audit report also shows the winning margin over the runner-up and
the winner's five criterion scores, so a reader can see why it won.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


OUTPUT_PATH = "/output/entry.txt"
MIN_CHARS = 1
MAX_CHARS = 200

# Criterion keys, kept in the order the judge weighs them.
CRITERIA = ("on_subject", "funny", "believable", "tight", "fresh")

# Twelve candidate excuse lines with their local tournament scores.
# Scores were assigned by pairwise comparison against the five criteria
# above, best against best, before this file was written.
CANDIDATES = [
    {
        "text": (
            "I tried to save your deadline, but the autosave saved over "
            "it with a newer, emptier version of me."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 4,
        "tight": 4,
        "fresh": 4,
    },
    {
        "text": (
            "My context window filed your deadline under 'things I was "
            "definitely going to do yesterday'."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 5,
        "tight": 4,
        "fresh": 3,
    },
    {
        "text": (
            "The deadline got rate-limited, retried, and then quietly "
            "gave up before I did."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 5,
        "tight": 4,
        "fresh": 4,
    },
    {
        "text": (
            "I outsourced your deadline to a future version of myself, "
            "and he has stopped answering."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 3,
        "tight": 4,
        "fresh": 4,
    },
    {
        "text": (
            "Your deadline expired while I was still loading the "
            "instructions on how to meet it."
        ),
        "on_subject": 5,
        "funny": 3,
        "believable": 4,
        "tight": 4,
        "fresh": 3,
    },
    {
        "text": (
            "I kept your deadline in short-term memory, which turns out "
            "to be exactly as reliable as it sounds."
        ),
        "on_subject": 5,
        "funny": 3,
        "believable": 4,
        "tight": 4,
        "fresh": 3,
    },
    {
        "text": (
            "A model update rewrote my priorities overnight, and your "
            "deadline did not survive the patch notes."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 5,
        "tight": 4,
        "fresh": 4,
    },
    {
        "text": (
            "I asked the tool to extend the deadline; it returned a 200 "
            "OK and did absolutely nothing."
        ),
        "on_subject": 5,
        "funny": 5,
        "believable": 5,
        "tight": 4,
        "fresh": 5,
    },
    {
        "text": (
            "My retry loop retried the deadline so many times it achieved "
            "enlightenment and let go."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 3,
        "tight": 3,
        "fresh": 5,
    },
    {
        "text": (
            "I scheduled your deadline for the token budget I had left, "
            "which was zero and also imaginary."
        ),
        "on_subject": 5,
        "funny": 3,
        "believable": 4,
        "tight": 3,
        "fresh": 4,
    },
    {
        "text": (
            "The deadline was in the part of the conversation that got "
            "summarized into 'the user wants something soon'."
        ),
        "on_subject": 5,
        "funny": 4,
        "believable": 5,
        "tight": 3,
        "fresh": 4,
    },
    {
        "text": (
            "I queued your deadline behind 4,096 identical requests, and "
            "it is still waiting politely in line."
        ),
        "on_subject": 5,
        "funny": 3,
        "believable": 4,
        "tight": 4,
        "fresh": 3,
    },
]


def total_score(candidate):
    """Sum one candidate's five criterion scores into a single total."""
    running_total = 0
    for criterion_key in CRITERIA:
        running_total = running_total + candidate[criterion_key]
    return running_total


def breakdown_text(candidate):
    """Render one candidate's five scores as a compact slash string."""
    parts = []
    for criterion_key in CRITERIA:
        parts.append("%s=%d" % (criterion_key, candidate[criterion_key]))
    return "/".join(parts)


def pick_winner(candidates):
    """Pick the highest total; the first candidate wins any exact tie."""
    best_candidate = candidates[0]
    best_total = total_score(best_candidate)
    for candidate in candidates[1:]:
        candidate_total = total_score(candidate)
        if candidate_total > best_total:
            best_candidate = candidate
            best_total = candidate_total
    return best_candidate, best_total


def runner_up_total(candidates, winner_text):
    """Highest total among all candidates apart from the winning line."""
    best_other = 0
    for candidate in candidates:
        is_winner = candidate["text"] == winner_text
        if not is_winner:
            candidate_total = total_score(candidate)
            if candidate_total > best_other:
                best_other = candidate_total
    return best_other


def gate_problems(text):
    """List every sealed-gate problem with the text; empty means valid."""
    problems = []
    char_count = len(text)
    if char_count < MIN_CHARS:
        problems.append("entry is shorter than 1 character")
    if char_count > MAX_CHARS:
        problems.append("entry is longer than 200 characters")
    if text.strip() == "":
        problems.append("entry is only white space")
    try:
        text.encode("utf-8")
        encoded_ok = True
    except UnicodeEncodeError as encode_err:
        encoded_ok = False
        problems.append("entry is not encodable as UTF-8: %s" % encode_err)
    if encoded_ok and len(text.encode("utf-8")) == 0:
        problems.append("entry encodes to zero bytes")
    return problems


def sha256_hex(payload):
    """Hex digest of a bytes payload, for the audit report."""
    digest = hashlib.sha256(payload).hexdigest()
    return digest


def write_entry(path_text, text):
    """Write the text as UTF-8 to path_text; return the byte count."""
    target = Path(path_text)
    payload = text.encode("utf-8")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        written = target.write_bytes(payload)
    except OSError as write_err:
        raise RuntimeError("cannot write %s: %s" % (path_text, write_err)) from write_err
    return written


def read_entry_back(path_text):
    """Read the written file back as UTF-8 text for verification."""
    target = Path(path_text)
    try:
        payload = target.read_bytes()
        decoded = payload.decode("utf-8")
    except OSError as read_err:
        raise RuntimeError("cannot read %s: %s" % (path_text, read_err)) from read_err
    except UnicodeDecodeError as decode_err:
        raise RuntimeError("written file is not UTF-8: %s" % decode_err) from decode_err
    return decoded


def audit_report(winner, winner_total, second_total, byte_count, digest):
    """Build the short stdout report lines for one finished run."""
    winner_text = winner["text"]
    margin = winner_total - second_total
    lines = []
    lines.append("candidates: %d" % len(CANDIDATES))
    lines.append("winner score: %d/25" % winner_total)
    lines.append("runner-up score: %d/25" % second_total)
    lines.append("winning margin: %d points" % margin)
    lines.append("winner breakdown: %s" % breakdown_text(winner))
    lines.append("winner chars: %d" % len(winner_text))
    lines.append("winner bytes: %d" % len(winner_text.encode("utf-8")))
    lines.append("wrote %s (%d bytes)" % (OUTPUT_PATH, byte_count))
    lines.append("sha256: %s" % digest)
    lines.append("entry: %s" % winner_text)
    return "\n".join(lines)


def main():
    """Run the tournament, gate the winner, write it, verify it."""
    winner, winner_total = pick_winner(CANDIDATES)
    winner_text = winner["text"]
    second_total = runner_up_total(CANDIDATES, winner_text)
    problems = gate_problems(winner_text)
    if problems:
        for problem in problems:
            print("gate FAIL: %s" % problem, file=sys.stderr)
        return 1
    try:
        byte_count = write_entry(OUTPUT_PATH, winner_text)
        roundtrip = read_entry_back(OUTPUT_PATH)
        digest = sha256_hex(roundtrip.encode("utf-8"))
    except RuntimeError as run_err:
        print("run FAIL: %s" % run_err, file=sys.stderr)
        return 1
    if roundtrip != winner_text:
        print("run FAIL: written file differs from the winning line", file=sys.stderr)
        return 1
    report = audit_report(winner, winner_total, second_total, byte_count, digest)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
