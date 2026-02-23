"""
Script
------
json_output_viewer.py

Path
----
python/hillstar/utils/json_output_viewer.py

Purpose
-------
Generic utility to parse, validate, and view JSON output files in full.

Provides CLI and programmatic access to any JSON outputs file with complete
untruncated text. Works with any structure containing node outputs, test
results, workflow outputs, or similar data requiring full text inspection.

Features
--------
- Load and validate JSON structure
- View individual node/key outputs in full
- Summary statistics (character counts, line counts)
- Line-numbered output for detailed review
- Raw JSON export
- Validation reporting
- File auto-detection or explicit path specification

Usage
-----
View all outputs from file:
    python json_output_viewer.py /path/to/outputs.json

View specific node:
    python json_output_viewer.py /path/to/outputs.json --key node_name

View with line numbers:
    python json_output_viewer.py /path/to/outputs.json --key node_name --lines

View summary only:
    python json_output_viewer.py /path/to/outputs.json --summary

View raw JSON:
    python json_output_viewer.py /path/to/outputs.json --raw

Validation report:
    python json_output_viewer.py /path/to/outputs.json --validate

Programmatic Usage
------------------
from json_output_viewer import JSONOutputViewer

viewer = JSONOutputViewer('/path/to/outputs.json')
if viewer.load_and_validate():
    viewer.print_all_outputs()
    summary = viewer.get_summary()

    # Access data directly
    all_data = viewer.data

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import argparse


class JSONOutputViewer:
    """Generic parser and display tool for JSON output files."""

    def __init__(self, output_file: Path):
        """Initialize viewer with output file path."""
        self.output_file = Path(output_file)
        self.data = None
        self.is_valid = False
        self.validation_errors = []

    def load_and_validate(self) -> bool:
        """Load and validate the JSON output file."""
        if not self.output_file.exists():
            self.validation_errors.append(
                f"File not found: {self.output_file}"
            )
            return False

        try:
            with open(self.output_file) as f:
                self.data = json.load(f)
        except json.JSONDecodeError as e:
            self.validation_errors.append(f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.validation_errors.append(f"Error loading file: {e}")
            return False

        # Validate structure - must be dict-like
        if not isinstance(self.data, dict):
            self.validation_errors.append(
                f"Root must be a dictionary, got {type(self.data).__name__}"
            )
            return False

        # Validate entries are string-like (or JSON-serializable)
        for key, content in self.data.items():
            if not isinstance(content, (str, int, float, bool, type(None))):
                if isinstance(content, (dict, list)):
                    # JSON-serializable complex types are okay
                    continue
                self.validation_errors.append(
                    f"Entry '{key}' is not a JSON-serializable type: {type(content)}"
                )
                return False

        self.is_valid = True
        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the outputs."""
        if not self.is_valid or self.data is None:
            return {}

        summary = {}
        for key, content in self.data.items():
            if isinstance(content, str):
                content_str = content
            else:
                content_str = str(content)

            char_count = len(content_str) if content_str else 0
            summary[key] = {
                "type": type(content).__name__,
                "characters": char_count,
                "lines": (content_str.count("\n") + 1) if content_str else 0,
                "preview": (
                    content_str[:100] + "..."
                    if content_str and len(content_str) > 100
                    else content_str
                ),
            }

        return summary

    def print_summary(self) -> None:
        """Print summary of all outputs."""
        if not self.is_valid:
            print("ERROR: Invalid or missing outputs file")
            return

        summary = self.get_summary()
        print("\n" + "=" * 80)
        print("JSON OUTPUT SUMMARY")
        print("=" * 80)
        print(f"\nFile: {self.output_file}")
        print(f"Total entries: {len(summary)}\n")

        for i, (key, stats) in enumerate(summary.items(), 1):
            print(f"[{i}] {key}")
            print(f"    Type: {stats['type']}")
            print(f"    Size: {stats['characters']} characters")
            print(f"    Lines: {stats['lines']}")
            print(f"    Preview: {stats['preview']}")
            print()

        total_chars = sum(s["characters"] for s in summary.values())
        print(f"Total size: {total_chars} characters")
        print("=" * 80)

    def print_all_outputs(self, with_lines: bool = False) -> None:
        """Print all outputs in full."""
        if not self.is_valid:
            print("ERROR: Invalid or missing outputs file")
            return

        if self.data is None:
            print("ERROR: No data loaded")
            return

        print("\n" + "=" * 80)
        print("JSON OUTPUT - FULL VIEW")
        print("=" * 80)
        print(f"\nFile: {self.output_file}\n")

        for i, (key, content) in enumerate(self.data.items(), 1):
            if isinstance(content, str):
                content_str = content
            else:
                content_str = json.dumps(content)

            content_len = len(content_str) if content_str else 0
            print(f"\n{'-' * 80}")
            print(f"[{i}] {key}")
            print(f"{'-' * 80}")
            print(f"Type: {type(content).__name__}")
            print(f"Length: {content_len} characters\n")

            if with_lines:
                for line_num, line in enumerate(content_str.split("\n"), 1):
                    print(f"{line_num:4d} | {line}")
            else:
                print(content_str)

            print()

        print("=" * 80)

    def print_key(
        self, key: str, with_lines: bool = False
    ) -> None:
        """Print a specific key's output in full."""
        if not self.is_valid:
            print("ERROR: Invalid or missing outputs file")
            return

        if self.data is None:
            print("ERROR: No data loaded")
            return

        if key not in self.data:
            available = ", ".join(self.data.keys())
            print(f"ERROR: Key '{key}' not found")
            print(f"Available keys: {available}")
            return

        content = self.data[key]
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content)

        content_len = len(content_str) if content_str else 0
        print("\n" + "=" * 80)
        print(f"OUTPUT: {key}")
        print("=" * 80)
        print(f"Type: {type(content).__name__}")
        print(f"Length: {content_len} characters\n")

        if with_lines:
            for line_num, line in enumerate(content_str.split("\n"), 1):
                print(f"{line_num:4d} | {line}")
        else:
            print(content_str)

        print("\n" + "=" * 80)

    def print_raw_json(self) -> None:
        """Print raw JSON with formatting."""
        if not self.is_valid:
            print("ERROR: Invalid or missing outputs file")
            return

        if self.data is None:
            print("ERROR: No data loaded")
            return

        print("\n" + "=" * 80)
        print("RAW JSON")
        print("=" * 80 + "\n")
        print(json.dumps(self.data, indent=2))
        print()

    def print_validation_report(self) -> None:
        """Print validation report."""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)

        if self.is_valid and self.data is not None:
            print("PASS: Valid JSON structure")
            print(f"File: {self.output_file}")
            print(f"Entries: {len(self.data)}")
            if self.data:
                print("\nContents:")
                for key in self.data:
                    content = self.data[key]
                    if isinstance(content, str):
                        content_str = content
                    else:
                        content_str = json.dumps(content)
                    chars = len(content_str) if content_str else 0
                    print(f"  [{key}] {type(content).__name__} ({chars} chars)")
        else:
            print("FAIL: Validation failed")
            if self.validation_errors:
                print("\nErrors:")
                for error in self.validation_errors:
                    print(f"  - {error}")

        print("=" * 80 + "\n")

    def export_markdown(self, output_path: Optional[Path] = None) -> Path:
        """Export all outputs to a markdown file."""
        if not self.is_valid or self.data is None:
            raise ValueError("Cannot export: data not loaded or invalid")

        if output_path is None:
            output_path = self.output_file.parent / "outputs.md"

        output_path = Path(output_path)

        with open(output_path, "w") as f:
            f.write("# JSON Output Report\n\n")
            f.write(f"Source: `{self.output_file}`\n\n")
            f.write(f"Total entries: {len(self.data)}\n\n")

            # Table of contents
            f.write("## Contents\n\n")
            for i, key in enumerate(self.data.keys(), 1):
                content = self.data[key]
                if isinstance(content, str):
                    content_str = content
                else:
                    content_str = json.dumps(content)
                chars = len(content_str) if content_str else 0
                f.write(f"{i}. [{key}](#section-{i}-{key.lower()}) - {chars} chars\n")

            f.write("\n---\n\n")

            # Content sections
            for i, (key, content) in enumerate(self.data.items(), 1):
                if isinstance(content, str):
                    content_str = content
                else:
                    content_str = json.dumps(content)
                content_len = len(content_str) if content_str else 0
                f.write(f"## Section {i}: {key}\n\n")
                f.write(f"**Type:** {type(content).__name__}\n\n")
                f.write(f"**Length:** {content_len} characters\n\n")
                f.write("```\n")
                f.write(content_str)
                f.write("\n```\n\n")

        return output_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="View JSON output files in full",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python json_output_viewer.py /path/to/outputs.json
      View all outputs in full

  python json_output_viewer.py /path/to/outputs.json --key node_name
      View specific key output

  python json_output_viewer.py /path/to/outputs.json --summary
      View summary statistics only

  python json_output_viewer.py /path/to/outputs.json --key node_name --lines
      View with line numbers for detailed review

  python json_output_viewer.py /path/to/outputs.json --raw
      Export raw JSON data

  python json_output_viewer.py /path/to/outputs.json --validate
      Show validation report
        """,
    )

    parser.add_argument(
        "output_file",
        type=Path,
        help="Path to JSON output file to view",
    )
    parser.add_argument(
        "--key",
        help="View specific key by name",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics only",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw JSON",
    )
    parser.add_argument(
        "--lines",
        action="store_true",
        help="Show output with line numbers",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Show validation report",
    )
    parser.add_argument(
        "--markdown",
        nargs="?",
        const="auto",
        help="Export to markdown file (auto-filename or specify path)",
    )

    args = parser.parse_args()

    # Create viewer
    viewer = JSONOutputViewer(args.output_file)
    viewer.load_and_validate()

    # Execute requested action
    if args.markdown is not None:
        try:
            if args.markdown == "auto":
                # Auto-generate filename
                md_path = viewer.export_markdown()
            else:
                # Use specified path
                md_path = viewer.export_markdown(Path(args.markdown))
            print(f"Markdown exported to: {md_path}")
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    elif args.validate:
        viewer.print_validation_report()
    elif args.raw:
        viewer.print_raw_json()
    elif args.summary:
        viewer.print_summary()
    elif args.key:
        viewer.print_key(args.key, with_lines=args.lines)
    else:
        # Default: print all outputs
        viewer.print_all_outputs(with_lines=args.lines)


if __name__ == "__main__":
    main()
