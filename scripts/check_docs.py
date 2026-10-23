"""Validate repository Markdown file links without contacting external websites."""

from pathlib import Path
import re


def main():
    root = Path(__file__).resolve().parents[1]
    errors = []
    files = [
        root / "README.md",
        root / "EVALUATION.md",
        *sorted((root / "docs").rglob("*.md")),
    ]
    for file in files:
        for target in re.findall(
            r"!?\[[^\]]*\]\(([^)]+)\)", file.read_text(encoding="utf-8")
        ):
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            path = target.split("#")[0]
            if path and not (file.parent / path).exists():
                errors.append(f"{file.relative_to(root)}: {target}")
    if errors:
        raise ValueError("Broken local documentation links:\n" + "\n".join(errors))
    print(
        f"Local links valid in {len(files)} Markdown files; external links/anchors not checked"
    )


if __name__ == "__main__":
    main()
