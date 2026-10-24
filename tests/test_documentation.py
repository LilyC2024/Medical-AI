"""Source documentation checks, no browser/network or clinical data."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "lovisa_doc_check", Path(__file__).parents[1] / "scripts/check_docs.py"
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def test_heading_anchors_include_duplicates_unicode_and_literal_code():
    text = "# Upload/Analyze: `CT`\n## Review\n## Review\n## 中文 指南\n```md\n## Ignored\n```\n"
    assert checker.anchors(text) == {
        "uploadanalyze-ct",
        "review",
        "review-1",
        "中文-指南",
    }


def test_local_heading_and_percent_encoded_path_are_checked(tmp_path):
    (tmp_path / "README.md").write_text(
        "[API](docs/My%20Guide.md#input--output)\n[local](#top)\n# Top\n"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/My Guide.md").write_text("## Input & output\n")
    files, errors = checker.validate(tmp_path)
    assert len(files) == 2 and not errors
    (tmp_path / "docs/My Guide.md").write_text("## Changed\n")
    assert checker.validate(tmp_path)[1] == [
        "README.md: missing heading docs/My%20Guide.md#input--output"
    ]


def test_missing_local_targets_fail_but_remote_and_fenced_examples_are_ignored(
    tmp_path,
):
    (tmp_path / "README.md").write_text(
        "[remote](https://example.invalid/unavailable)\n[bad](missing.md)\n```md\n[example](not-a-file.md)\n```\n"
    )
    assert checker.validate(tmp_path)[1] == ["README.md: missing file missing.md"]


def test_directory_links_are_valid_github_navigation(tmp_path):
    (tmp_path / "README.md").write_text("[Tests](tests)\n")
    (tmp_path / "tests").mkdir()
    assert not checker.validate(tmp_path)[1]
