#!/usr/bin/env python3
"""Initialize and validate a lightweight PDDR workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


DECISION_STATUSES = {
    "proposed",
    "accepted",
    "rejected",
    "superseded",
    "needs-confirmation",
}
DELIVERY_STATUSES = {
    "not-started",
    "in-progress",
    "implemented",
    "validated",
    "not-applicable",
    "unknown",
}
SCOPES = {"project", "product", "process"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "decision_date",
    "recorded_date",
    "decision_status",
    "delivery_status",
    "scope",
    "owners",
    "evidence",
    "related",
    "supersedes",
    "superseded_by",
}
REQUIRED_SECTIONS = {
    "Summary",
    "Context and observations",
    "Options considered",
    "Decision",
    "Delivery and validation",
    "Consequences",
    "Revisit when",
    "Evidence",
    "Related records",
}
LIST_FIELDS = {"scope", "owners", "evidence", "related", "supersedes"}
ID_PATTERN = re.compile(r"^PDDR-(\d{4})$")
FILENAME_PATTERN = re.compile(r"^(PDDR-\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
KIT_VERSION = "0.2.1"
MANIFEST_SCHEMA_VERSION = 1
MANAGED_PATHS = (
    ".pddr/pddr.py",
    ".pddr/specification.md",
    ".pddr/template.md",
)


@dataclass(frozen=True)
class Diagnostic:
    path: Path
    message: str


class FrontMatterError(ValueError):
    pass


def _sha256(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _source_files(script_path: Path) -> dict[str, bytes]:
    kit_root = script_path.parents[1]
    template_source = kit_root / "templates" / "pddr.md"
    specification_source = kit_root / "docs" / "specification.md"
    if not template_source.is_file() or not specification_source.is_file():
        template_source = script_path.parent / "template.md"
        specification_source = script_path.parent / "specification.md"
    if not template_source.is_file() or not specification_source.is_file():
        raise ValueError("PDDR template or specification could not be found")
    return {
        ".pddr/pddr.py": script_path.read_bytes(),
        ".pddr/specification.md": specification_source.read_bytes(),
        ".pddr/template.md": template_source.read_bytes(),
    }


def _manifest(contents: dict[str, bytes], *, kit_version: str = KIT_VERSION) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "kit_version": kit_version,
        "managed_files": {path: _sha256(contents[path]) for path in sorted(contents)},
    }


def _manifest_bytes(contents: dict[str, bytes], *, kit_version: str = KIT_VERSION) -> bytes:
    return (json.dumps(_manifest(contents, kit_version=kit_version), indent=2) + "\n").encode()


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"{path} has an unsupported schema_version")
    managed_files = manifest.get("managed_files")
    if not isinstance(managed_files, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in managed_files.items()
    ):
        raise ValueError(f"{path} must contain a managed_files object")
    for relative_path in managed_files:
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"{path} contains an unsafe managed path: {relative_path}")
    return manifest


def _scalar(value: str) -> Any:
    value = value.strip()
    if value in {"null", "~"}:
        return None
    if value == "[]":
        return []
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontMatterError("front matter must start with '---'")

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise FrontMatterError("front matter is missing its closing '---'") from exc

    metadata: dict[str, Any] = {}
    active_list: str | None = None
    for number, raw_line in enumerate(lines[1:end], start=2):
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            item = re.match(r"^\s+-\s+(.+?)\s*$", line)
            if not item or active_list is None:
                raise FrontMatterError(f"unsupported nested value on line {number}")
            metadata[active_list].append(_scalar(item.group(1)))
            continue

        match = re.match(r"^([a-z][a-z0-9_]*):(?:\s*(.*))?$", line)
        if not match:
            raise FrontMatterError(f"invalid metadata on line {number}")
        key, raw_value = match.groups()
        if key in metadata:
            raise FrontMatterError(f"duplicate metadata field '{key}'")
        if raw_value:
            metadata[key] = _scalar(raw_value)
            active_list = None
        else:
            metadata[key] = []
            active_list = key

    return metadata, "\n".join(lines[end + 1 :])


def _is_iso_date(value: Any, *, allow_unknown: bool) -> bool:
    if allow_unknown and value == "unknown":
        return True
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _section_has_content(body: str, heading: str) -> bool:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return False
    content = re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL)
    return bool(content.strip())


def validate_record(path: Path) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [Diagnostic(path, f"cannot read UTF-8 file: {exc}")]

    try:
        metadata, body = parse_front_matter(text)
    except FrontMatterError as exc:
        return None, [Diagnostic(path, str(exc))]

    missing = sorted(REQUIRED_FIELDS - metadata.keys())
    if missing:
        diagnostics.append(Diagnostic(path, f"missing metadata: {', '.join(missing)}"))

    record_id = metadata.get("id")
    if not isinstance(record_id, str) or not ID_PATTERN.fullmatch(record_id):
        diagnostics.append(Diagnostic(path, "id must match PDDR-NNNN"))

    filename = FILENAME_PATTERN.fullmatch(path.name)
    if not filename:
        diagnostics.append(
            Diagnostic(path, "filename must match PDDR-NNNN-short-kebab-title.md")
        )
    elif record_id != filename.group(1):
        diagnostics.append(Diagnostic(path, "front matter id does not match filename id"))

    if not isinstance(metadata.get("title"), str) or not metadata.get("title", "").strip():
        diagnostics.append(Diagnostic(path, "title must be a non-empty string"))
    if not _is_iso_date(metadata.get("decision_date"), allow_unknown=True):
        diagnostics.append(Diagnostic(path, "decision_date must be YYYY-MM-DD or unknown"))
    if not _is_iso_date(metadata.get("recorded_date"), allow_unknown=False):
        diagnostics.append(Diagnostic(path, "recorded_date must be YYYY-MM-DD"))

    if metadata.get("decision_status") not in DECISION_STATUSES:
        diagnostics.append(Diagnostic(path, "decision_status is not an allowed value"))
    if metadata.get("delivery_status") not in DELIVERY_STATUSES:
        diagnostics.append(Diagnostic(path, "delivery_status is not an allowed value"))

    for field in sorted(LIST_FIELDS):
        if field in metadata and not isinstance(metadata[field], list):
            diagnostics.append(Diagnostic(path, f"{field} must be a list"))
    scope = metadata.get("scope")
    if isinstance(scope, list):
        invalid_scopes = sorted({str(item) for item in scope} - SCOPES)
        if not scope:
            diagnostics.append(Diagnostic(path, "scope must contain at least one value"))
        if invalid_scopes:
            diagnostics.append(
                Diagnostic(path, f"scope contains invalid values: {', '.join(invalid_scopes)}")
            )

    superseded_by = metadata.get("superseded_by")
    if superseded_by is not None and (
        not isinstance(superseded_by, str) or not ID_PATTERN.fullmatch(superseded_by)
    ):
        diagnostics.append(Diagnostic(path, "superseded_by must be null or a PDDR-NNNN id"))
    if metadata.get("decision_status") == "superseded" and superseded_by is None:
        diagnostics.append(Diagnostic(path, "superseded records must set superseded_by"))

    headings = set(re.findall(r"^## (.+?)\s*$", body, flags=re.MULTILINE))
    missing_sections = sorted(REQUIRED_SECTIONS - headings)
    if missing_sections:
        diagnostics.append(
            Diagnostic(path, f"missing sections: {', '.join(missing_sections)}")
        )

    evidence = metadata.get("evidence")
    if metadata.get("delivery_status") == "validated":
        if not isinstance(evidence, list) or not evidence:
            diagnostics.append(Diagnostic(path, "validated records need metadata evidence"))
        if not _section_has_content(body, "Delivery and validation"):
            diagnostics.append(
                Diagnostic(path, "validated records need delivery and validation details")
            )

    return metadata, diagnostics


def resolve_records_dir(target: Path, override: str | None) -> Path:
    if override:
        records_dir = Path(override)
        if records_dir.is_absolute() or ".." in records_dir.parts:
            raise ValueError("--records-dir must be a relative path inside the target")
        return target / records_dir
    config_path = target / ".pddr" / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read {config_path}: {exc}") from exc
        records_dir = config.get("records_dir")
        if not isinstance(records_dir, str) or not records_dir.strip():
            raise ValueError(f"{config_path} must contain a non-empty records_dir")
        configured_path = Path(records_dir)
        if configured_path.is_absolute() or ".." in configured_path.parts:
            raise ValueError(f"{config_path} records_dir must stay inside the target")
        return target / configured_path
    return target / "docs" / "records"


def command_validate(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    try:
        records_dir = resolve_records_dir(target, args.records_dir)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not records_dir.is_dir():
        print(f"error: records directory does not exist: {records_dir}", file=sys.stderr)
        return 2

    records = sorted(records_dir.glob("PDDR-*.md"))
    if not records:
        if args.allow_empty:
            print(f"OK: no PDDR records found in {records_dir}")
            return 0
        print(f"error: no PDDR records found in {records_dir}", file=sys.stderr)
        return 2

    diagnostics: list[Diagnostic] = []
    seen_ids: dict[str, Path] = {}
    parsed: list[tuple[Path, dict[str, Any]]] = []
    for record in records:
        metadata, record_diagnostics = validate_record(record)
        diagnostics.extend(record_diagnostics)
        if metadata is None:
            continue
        parsed.append((record, metadata))
        record_id = metadata.get("id")
        if isinstance(record_id, str):
            if record_id in seen_ids:
                diagnostics.append(
                    Diagnostic(record, f"duplicate id also used by {seen_ids[record_id].name}")
                )
            else:
                seen_ids[record_id] = record

    known_ids = set(seen_ids)
    for record, metadata in parsed:
        references = (
            list(metadata.get("supersedes", []))
            if isinstance(metadata.get("supersedes"), list)
            else []
        )
        if metadata.get("superseded_by") is not None:
            references.append(metadata["superseded_by"])
        for reference in references:
            if (
                isinstance(reference, str)
                and ID_PATTERN.fullmatch(reference)
                and reference not in known_ids
            ):
                diagnostics.append(
                    Diagnostic(record, f"record reference does not exist: {reference}")
                )

    for diagnostic in diagnostics:
        try:
            display_path = diagnostic.path.relative_to(target)
        except ValueError:
            display_path = diagnostic.path
        print(f"{display_path}: {diagnostic.message}", file=sys.stderr)
    if diagnostics:
        print(f"FAILED: {len(diagnostics)} issue(s) in {len(records)} record(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(records)} PDDR record(s) validated")
    return 0


def command_init(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"error: target directory does not exist: {target}", file=sys.stderr)
        return 2

    script_path = Path(__file__).resolve()
    try:
        managed_contents = _source_files(script_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    records_dir = Path(args.records_dir)
    if records_dir.is_absolute() or ".." in records_dir.parts:
        print("error: --records-dir must be a relative path inside the target", file=sys.stderr)
        return 2

    config = {
        "records_dir": records_dir.as_posix(),
        "specification": ".pddr/specification.md",
        "template": ".pddr/template.md",
    }
    readme = (
        "# PDDR records\n\n"
        "Project Design Decision Records for this repository live in this directory. "
        "Create a record from `.pddr/template.md` and validate it with "
        "`python .pddr/pddr.py validate`.\n"
    )
    outputs: list[tuple[Path, bytes]] = [
        (target / ".pddr" / "config.json", (json.dumps(config, indent=2) + "\n").encode()),
        (target / ".pddr" / "manifest.json", _manifest_bytes(managed_contents)),
        *[(target / path, content) for path, content in managed_contents.items()],
        (target / records_dir / "README.md", readme.encode()),
    ]

    conflicts = [
        path for path, content in outputs if path.exists() and path.read_bytes() != content
    ]
    if conflicts:
        for path in conflicts:
            print(f"conflict: existing file differs: {path}", file=sys.stderr)
        print("No files were changed.", file=sys.stderr)
        return 1

    action = "Would create" if args.dry_run else "Created"
    for path, content in outputs:
        if path.exists():
            print(f"Unchanged: {path.relative_to(target)}")
            continue
        print(f"{action}: {path.relative_to(target)}")
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    return 0


def command_upgrade(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"error: target directory does not exist: {target}", file=sys.stderr)
        return 2

    script_path = Path(__file__).resolve()
    installed_script = target / ".pddr" / "pddr.py"
    if script_path == installed_script.resolve():
        print(
            "error: run upgrade from a newer PDDR Kit checkout, not the installed copy",
            file=sys.stderr,
        )
        return 2
    try:
        new_contents = _source_files(script_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    manifest_path = target / ".pddr" / "manifest.json"
    if args.bootstrap_manifest:
        if manifest_path.exists():
            print(f"error: manifest already exists: {manifest_path}", file=sys.stderr)
            return 2
        current_contents: dict[str, bytes] = {}
        missing: list[Path] = []
        for relative_path in MANAGED_PATHS:
            path = target / relative_path
            if path.is_symlink() or not path.is_file():
                missing.append(path)
            else:
                current_contents[relative_path] = path.read_bytes()
        if missing:
            for path in missing:
                print(f"error: managed file does not exist: {path}", file=sys.stderr)
            return 2
        action = "Would create" if args.dry_run else "Created"
        print(f"{action}: .pddr/manifest.json")
        if not args.dry_run:
            manifest_path.write_bytes(_manifest_bytes(current_contents, kit_version="legacy"))
        print("No managed files were changed.")
        return 0

    if not manifest_path.is_file():
        print(
            "error: installation manifest is missing; review the installed managed files, "
            "then run upgrade --bootstrap-manifest first",
            file=sys.stderr,
        )
        return 2
    try:
        installed_manifest = _load_manifest(manifest_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    expected_hashes: dict[str, str] = installed_manifest["managed_files"]
    conflicts: list[Path] = []
    for relative_path, expected_hash in expected_hashes.items():
        path = target / relative_path
        if path.is_symlink() or not path.is_file() or _sha256(path.read_bytes()) != expected_hash:
            conflicts.append(path)
    for relative_path in new_contents.keys() - expected_hashes.keys():
        path = target / relative_path
        if path.exists() or path.is_symlink():
            conflicts.append(path)
    if conflicts:
        for path in sorted(conflicts):
            print(f"conflict: managed file was changed or is untracked: {path}", file=sys.stderr)
        print("No files were changed.", file=sys.stderr)
        return 1

    changes = [
        relative_path
        for relative_path, content in new_contents.items()
        if not (target / relative_path).is_file()
        or (target / relative_path).read_bytes() != content
    ]
    for relative_path in sorted(new_contents):
        if relative_path in changes:
            action = "Would update" if args.dry_run else "Updated"
            print(f"{action}: {relative_path}")
        else:
            print(f"Unchanged: {relative_path}")
    if args.dry_run:
        if installed_manifest != _manifest(new_contents):
            print("Would update: .pddr/manifest.json")
        return 0

    for relative_path in changes:
        path = target / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(new_contents[relative_path])
    manifest_path.write_bytes(_manifest_bytes(new_contents))
    print(f"Installed PDDR Kit {KIT_VERSION}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pddr", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize PDDR files without overwriting")
    init_parser.add_argument("--target", default=".", help="project root (default: current directory)")
    init_parser.add_argument(
        "--records-dir", default="docs/records", help="records directory relative to target"
    )
    init_parser.add_argument("--dry-run", action="store_true", help="show changes only")
    init_parser.set_defaults(handler=command_init)

    upgrade_parser = subparsers.add_parser(
        "upgrade", help="safely update files managed by PDDR Kit"
    )
    upgrade_parser.add_argument(
        "--target", default=".", help="project root (default: current directory)"
    )
    upgrade_parser.add_argument("--dry-run", action="store_true", help="show changes only")
    upgrade_parser.add_argument(
        "--bootstrap-manifest",
        action="store_true",
        help="record hashes for a reviewed legacy installation without updating files",
    )
    upgrade_parser.set_defaults(handler=command_upgrade)

    validate_parser = subparsers.add_parser("validate", help="validate PDDR records")
    validate_parser.add_argument(
        "--target", default=".", help="project root (default: current directory)"
    )
    validate_parser.add_argument("--records-dir", help="override the configured records directory")
    validate_parser.add_argument(
        "--allow-empty", action="store_true", help="succeed when the records directory is empty"
    )
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
