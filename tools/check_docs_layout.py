from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_MARKDOWN_EXCEPTIONS = {"README.md"}
REQUIRED_DOCS = [
    "docs/README.md",
    "docs/agent/rules.md",
    "docs/agent/doc_map.md",
    "docs/human/overview/project_status.md",
    "docs/human/overview/next_actions.md",
    "docs/human/operations/simulation_runbook.md",
]


def main() -> int:
    violations = []

    root_markdown = sorted(
        path.name
        for path in REPO_ROOT.glob("*.md")
        if path.name not in ROOT_MARKDOWN_EXCEPTIONS
    )
    if root_markdown:
        violations.append(
            "repo root must keep only README.md as project-level Markdown:\n"
            + "\n".join(f"- {name}" for name in root_markdown)
        )

    missing = [path for path in REQUIRED_DOCS if not (REPO_ROOT / path).is_file()]
    if missing:
        violations.append(
            "required canonical docs are missing:\n"
            + "\n".join(f"- {path}" for path in missing)
        )

    if violations:
        print("doc layout check failed")
        for violation in violations:
            print(violation)
        return 1

    print("doc layout check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
