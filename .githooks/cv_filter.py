#!/usr/bin/env python3
"""Keeps the real phone number in the CV out of git.

Git runs this as the `cv-private` filter (see .gitattributes and setup.sh):

  clean   working copy -> git. Empties `phone:` and shows a masked copy of the number instead
          (+386 ** *** 456), as a custom connection with a phone icon: RenderCV only accepts
          real numbers in `phone:`. The masked copy keeps the country code and the last group.
  smudge  git -> working copy. Puts the real number back from this clone's `git config cv.phone`.

The hooks also use it:

  phone    prints the real number in the CV read from stdin (empty when there is none)
  pattern  prints a regular expression that finds a number in any format
"""

import re
import subprocess
import sys

MARK = "# masked phone"  # ends every line the clean filter adds, so smudge can take them out again
PHONE = re.compile(r"^  phone:[ \t]*(\S.*?)\s*$")
EMPTY_PHONE = re.compile(r"^  phone:[ \t]*$")
CUSTOM = re.compile(r"^  custom_connections:[ \t]*$")


def mask(number: str) -> str:
    """+386 40 123 456 -> +386 ** *** 456: the country code and the last group stay."""
    parts = number.split()
    if len(parts) >= 3:
        return " ".join([parts[0], *(re.sub(r"\d", "*", p) for p in parts[1:-1]), parts[-1]])
    return number[:4] + re.sub(r"\d", "*", number[4:-3]) + number[-3:]


def real_phone(lines: list[str]) -> str | None:
    for line in lines:
        m = PHONE.match(line)
        if m and MARK not in line:
            return m.group(1).strip("'\"")
    return None


def clean(lines: list[str]) -> list[str]:
    number = real_phone(lines)
    if number is None:
        return lines  # no number, or already masked
    masked = mask(number).replace("'", "''")
    item = [
        f"    - placeholder: '{masked}'  {MARK}\n",
        f"      fontawesome_icon: phone  {MARK}\n",
        f"      url:  {MARK}\n",
    ]
    lines = [line for line in lines if MARK not in line]
    out = []
    has_custom = any(CUSTOM.match(line) for line in lines)
    for line in lines:
        if PHONE.match(line):
            out.append("  phone:\n")
            if not has_custom:
                out += [f"  custom_connections:  {MARK}\n", *item]
        elif CUSTOM.match(line):
            out += [line, *item]
        else:
            out.append(line)
    return out


def smudge(lines: list[str]) -> list[str]:
    number = subprocess.run(
        ["git", "config", "--get", "cv.phone"], capture_output=True, text=True
    ).stdout.strip()
    if not number or not any(MARK in line for line in lines):
        return lines  # a clone without the number keeps the masked copy
    out = []
    for line in lines:
        if MARK in line:
            continue
        out.append(f"  phone: {number}\n" if EMPTY_PHONE.match(line) else line)
    return out


def pattern(number: str) -> str:
    """The digits after the country code, with up to two other characters between any two."""
    parts = number.split()
    rest = "".join(parts[1:]) if len(parts) > 1 else number.lstrip("+")[3:]
    digits = re.sub(r"\D", "", rest).lstrip("0")
    return "[^0-9]{0,2}".join(digits)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    text = sys.stdin.buffer.read().decode("utf-8")
    lines = text.splitlines(keepends=True)
    if mode == "clean":
        result = "".join(clean(lines))
    elif mode == "smudge":
        result = "".join(smudge(lines))
    elif mode == "phone":
        result = real_phone(lines) or ""
    elif mode == "pattern":
        result = pattern(text.strip()) if text.strip() else ""
    else:
        sys.exit(f"usage: {sys.argv[0]} clean|smudge|phone|pattern < file")
    sys.stdout.buffer.write(result.encode("utf-8"))


if __name__ == "__main__":
    main()
