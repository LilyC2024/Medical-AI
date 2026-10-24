"""Check maintained Markdown links and heading anchors without network access.

This intentionally checks ordinary inline links, not a complete Markdown grammar.
It excludes fenced examples and never walks ignored datasets or environments.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK = re.compile(r'!?\[[^\]]*\]\((<[^>]*>|[^\s)]+)(?:\s+"[^"]*")?\)')
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+\s*)?$")


def prose(text):
    """Remove fenced code so example links/headings are not treated as active."""
    output, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            output.append("")
        else:
            output.append(line if fence is None else "")
    return "\n".join(output)


def anchors(text):
    """Approximate GitHub heading IDs, including repeated headings and Unicode."""
    result, counts = set(), {}
    for line in prose(text).splitlines():
        match = HEADING.match(line)
        if not match:
            continue
        label = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", match.group(1))
        label = html.unescape(re.sub(r"<[^>]+>", "", label)).lower()
        slug = "".join(c for c in label if c.isalnum() or c in "_ -").replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        result.add(slug if number == 0 else f"{slug}-{number}")
    result.update(re.findall(r'\bid=["\']([^"\']+)["\']', prose(text)))
    return result


def documents(root):
    """Select maintained guides only; local runtime Markdown is not publication."""
    root = Path(root)
    return sorted(
        {
            *root.glob("*.md"),
            *(root / "docs").rglob("*.md"),
            *(root / "third_party").rglob("*.md"),
            *(
                p
                for p in (root / "reports/README.md", root / "data/evidence/README.md")
                if p.is_file()
            ),
        }
    )


def validate(root):
    """Return broken local files/anchors; HTTPS links are deliberately not fetched."""
    errors, cache = [], {}
    root = Path(root).resolve()
    files = documents(root)
    for file in files:
        for match in LINK.finditer(prose(file.read_text(encoding="utf-8"))):
            target = match.group(1).strip("<>")
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            path = (file.parent / unquote(url.path)).resolve() if url.path else file
            if not path.exists():
                errors.append(f"{file.relative_to(root)}: missing file {target}")
            elif url.fragment and path.suffix.lower() == ".md":
                if path not in cache:
                    cache[path] = anchors(path.read_text(encoding="utf-8"))
                if unquote(url.fragment) not in cache[path]:
                    errors.append(f"{file.relative_to(root)}: missing heading {target}")
    return files, errors


def main():
    files, errors = validate(Path(__file__).resolve().parents[1])
    if errors:
        raise ValueError("Broken documentation references:\n" + "\n".join(errors))
    print(
        f"Local files and Markdown heading anchors valid in {len(files)} documents; external URLs not fetched"
    )


if __name__ == "__main__":
    main()
