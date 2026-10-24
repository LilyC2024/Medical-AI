"""Regenerate source-linked class/function references without importing the app.

Run --write after intentional source changes; --check fails on stale documentation.
Annotations and docstrings describe code, not verified clinical capabilities.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


def cell(text):
    """Keep source syntax inside one Markdown table cell."""
    return " ".join(str(text).split()).replace("|", "\\|").replace("`", "'")


def source_files(root):
    """Select maintained implementation, interfaces and scripts, not tests/data."""
    directories = ("medical_assistant", "src", "deploy", "scripts")
    return sorted(
        {
            *(
                p
                for name in directories
                for p in (root / name).rglob("*.py")
                if "__pycache__" not in p.parts
            ),
            *(p for p in (root / "app.py",) if p.is_file()),
        }
    )


def render(root):
    """Derive signatures, declared fields, docstrings and direct calls from AST."""
    lines = [
        "# Source API and subfunction reference",
        "",
        (
            "[Module guide](../CODE_REFERENCE.md)"
            if (root / "docs/CODE_REFERENCE.md").is_file()
            else "[Module guide](../lung/code-reference.md)"
        )
        + " · [Root overview](../../README.md)",
        "",
        "Generated from maintained Python source with `scripts/generate_api_docs.py`. "
        "This is a navigation/reference index; subject guides define operation and "
        "research boundaries. It imports no application, model or clinical data. "
        "Source links include exact lines; direct calls are static names, not a runtime trace.",
        "",
    ]
    for path in source_files(root):
        relative = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        lines += [
            f"## [{relative}](../../{relative})",
            "",
            ast.get_docstring(tree)
            or "Implementation module; see the linked source and module guide.",
            "",
        ]

        def walk(nodes, prefix=""):
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    lines.extend(
                        [
                            f"### [{prefix}{node.name}](../../{relative}#L{node.lineno})",
                            "",
                            ast.get_docstring(node)
                            or "Class contract is defined by the fields and methods below.",
                            "",
                        ]
                    )
                    fields = [
                        n
                        for n in node.body
                        if isinstance(n, ast.AnnAssign)
                        and isinstance(n.target, ast.Name)
                    ]
                    if fields:
                        lines.extend(
                            [
                                "| Declared field | Type | Default / constraint expression |",
                                "| --- | --- | --- |",
                            ]
                        )
                        for field in fields:
                            default = (
                                ast.unparse(field.value)
                                if field.value is not None
                                else "required / supplied by caller"
                            )
                            lines.append(
                                f"| `{cell(field.target.id)}` | `{cell(ast.unparse(field.annotation))}` | `{cell(default)}` |"
                            )
                        lines.append("")
                    walk(node.body, prefix + node.name + ".")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signature = node.name + "(" + ast.unparse(node.args) + ")"
                    if node.returns is not None:
                        signature += " → " + ast.unparse(node.returns)
                    lines.extend(
                        [
                            f"#### [{prefix}{node.name}](../../{relative}#L{node.lineno})",
                            "",
                            "`" + cell(signature) + "`",
                            "",
                        ]
                    )
                    doc = ast.get_docstring(node)
                    if doc:
                        lines.extend([doc, ""])
                    calls = []
                    for item in ast.walk(node):
                        if isinstance(item, ast.Call):
                            name = ast.unparse(item.func)
                            if len(name) < 70 and name not in calls:
                                calls.append(name)
                    if calls:
                        lines.extend(
                            [
                                "Static calls (including nested helper bodies): "
                                + ", ".join("`" + cell(x) + "`" for x in calls[:14])
                                + (
                                    " (additional calls in source)."
                                    if len(calls) > 14
                                    else "."
                                ),
                                "",
                            ]
                        )
                    raised = sorted(
                        {
                            ast.unparse(
                                n.exc.func if isinstance(n.exc, ast.Call) else n.exc
                            )
                            for n in ast.walk(node)
                            if isinstance(n, ast.Raise) and n.exc is not None
                        }
                    )
                    if raised:
                        lines.extend(
                            [
                                "Explicit raised conditions: "
                                + ", ".join("`" + cell(x) + "`" for x in raised)
                                + ". See source for triggers; called validators may raise additional exceptions.",
                                "",
                            ]
                        )
                    walk(node.body, prefix + node.name + ".")
                else:
                    walk(ast.iter_child_nodes(node), prefix)

        walk(tree.body)
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / "docs/reference/CALLABLES.md"
    content = render(root)
    if args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print("Updated", target.relative_to(root))
    elif not target.is_file() or target.read_text(encoding="utf-8") != content:
        raise SystemExit(
            "API reference is stale; run scripts/generate_api_docs.py --write"
        )
    else:
        print("API reference matches source signatures, fields and subfunctions")


if __name__ == "__main__":
    main()
