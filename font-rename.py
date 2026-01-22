#!/usr/bin/env python3
"""
Rename font files based on their internal metadata.

This script uses fonttools to read font metadata and rename font files
according to their family name, subfamily, or full name stored in the
font file's name table.

Examples:
    ./font-rename.py fonts/*.ttf
    ./font-rename.py --combined fonts/*.otf
    ./font-rename.py --dry-run --verbose fonts/*.ttf

Options:
    --combined    Use Family-Subfamily naming format
    --dry-run     Show what would be renamed without making changes
    --verbose     Show detailed information during processing

Requirements:
    pip install fonttools
"""
import argparse
import sys
import uuid
from pathlib import Path

try:
    from fontTools.ttLib import TTFont  # type: ignore
except ImportError:
    print("Error: fonttools is not installed.")
    print("Install it with: pip install fonttools")
    sys.exit(1)


def get_font_metadata(font_path, name_id=4):
    """ Extract font name from font file metadata.
        Args:
            font_path: Path to the font file
            name_id: Name table ID (4=Full name, 1=Family, 2=Subfamily)
        Returns: str: Font name or None if not found
    """
    try:
        font = TTFont(font_path)
        name_table = font['name']
        # Try Windows platform first (more common)
        for record in name_table.names:
            if record.nameID == name_id and record.platformID == 3:
                return record.string.decode('utf-16-be')
        # Fall back to Mac platform
        for record in name_table.names:
            if record.nameID == name_id and record.platformID == 1:
                return record.string.decode('mac-roman')
        font.close()
        return None
    except Exception as e:
        raise Exception(f"Failed to read font metadata: {e}")


def get_combined_name(font_path):
    """ Get font name as Family-Subfamily. """
    try:
        font = TTFont(font_path)
        name_table = font['name']
        family = None
        subfamily = None
        for record in name_table.names:
            if record.platformID == 3:  # Windows
                if record.nameID == 1:
                    family = record.string.decode('utf-16-be')
                elif record.nameID == 2:
                    subfamily = record.string.decode('utf-16-be')
        font.close()
        if family and subfamily:
            return f"{family}-{subfamily}"
        return family
    except Exception as e:
        raise Exception(f"Failed to read font metadata: {e}")


def sanitize_filename(name):
    """ Clean filename for filesystem compatibility.
        Args: name: Original name string
        Returns: str: Sanitized filename
    """
    # Replace spaces with hyphens or underscores
    name = name.replace(' ', '-')
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')
    # Keep only alphanumeric, hyphens, underscores, and periods
    name = ''.join(c for c in name if c.isalnum() or c in '-_.')
    return name


def rename_font_file(file_path, pattern='full', dry_run=False, preserve_case=False):
    """ Rename font file based on its metadata.
        Args:
            file_path: Path to the font file
            pattern: Naming pattern ('full', 'family', 'family-style')
            dry_run: If True, only show what would be done
            preserve_case: If True, preserve original case
        Returns: str: New file path or None if failed
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")
    # Get font name based on pattern
    if pattern == 'full':
        font_name = get_font_metadata(file_path, name_id=4)
    elif pattern == 'family':
        font_name = get_font_metadata(file_path, name_id=1)
    elif pattern == 'family-style':
        font_name = get_combined_name(file_path)
    else:
        raise ValueError(f"Unknown pattern: {pattern}")
    if not font_name:
        raise ValueError("Could not extract font name from metadata")
    # Sanitize and prepare new filename
    safe_name = sanitize_filename(font_name)
    if not preserve_case:
        # Optional: you can uncomment this to force lowercase
        # safe_name = safe_name.lower()
        pass
    # Preserve file extension
    ext = file_path.suffix
    new_filename = safe_name + ext
    new_path = file_path.parent / new_filename
    # Check if source and target are the same (ignoring case)
    if file_path.resolve() == new_path.resolve():
        print(f"Skipped (already named correctly): {file_path.name}")
        return str(file_path)
    # Check if this is a case-only rename
    is_case_only_rename = (file_path.parent == new_path.parent
        and file_path.name.lower() == new_filename.lower())
    # Check if file already exists (skip check for case-only renames)
    if not is_case_only_rename and new_path.exists():
        raise FileExistsError(f"Target file already exists: {new_path}")
    # Perform rename or dry run
    if dry_run:
        print("[DRY RUN] Would rename:")
        print(f"  From: {file_path.name}")
        print(f"  To:   {new_filename}")
        return str(new_path)
    else:
        # Handle case-only rename on case-insensitive filesystem
        if is_case_only_rename:
            # Two-step rename to handle case-only changes
            temp_name = f".tmp_{uuid.uuid4().hex}{ext}"
            temp_path = file_path.parent / temp_name
            try:
                file_path.rename(temp_path)
                temp_path.rename(new_path)
            except (OSError, FileExistsError):
                # Case-only rename failed (case-insensitive filesystem)
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.rename(file_path)
                print(f"⚠ Skipped (case-only rename not supported on this filesystem): {file_path.name}")
                return str(file_path)
        else:
            # Direct rename
            file_path.rename(new_path)
        print("✓ Renamed successfully:")
        print(f"  From: {file_path.name}")
        print(f"  To:   {new_filename}")
        return str(new_path)


if __name__ == '__main__':
    epilog = "Examples:"
    epilog = "  %(prog)s font.ttf\n"
    epilog = "  %(prog)s font.otf --pattern family-style\n"
    epilog = "  %(prog)s font.woff2 --dry-run\n"
    epilog = "  %(prog)s *.ttf --pattern family\n\n"
    epilog = "Naming patterns:\n"
    epilog = "  full          - Use full font name (Name ID 4) [default]\n"
    epilog = "  family        - Use font family name only (Name ID 1)\n"
    epilog = "  family-style  - Use family-subfamily (e.g., Roboto-Bold)\n"
    parser = argparse.ArgumentParser(
        description='Rename font files based on their internal metadata using fonttools.',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=epilog)
    parser.add_argument('filepaths', nargs='+', metavar='filepath', help='Path(s) to font file(s) to rename')
    parser.add_argument('-p', '--pattern', choices=['full', 'family', 'family-style'], default='full', help='Naming pattern to use (default: full)')  # noqa
    parser.add_argument('-d', '--dry-run', action='store_true', help='Show what would be done without actually renaming')  # noqa
    parser.add_argument('--preserve-case', action='store_true', help='Preserve original case in filename')
    args = parser.parse_args()
    # Process multiple files
    success_count = 0
    error_count = 0
    for filepath in args.filepaths:
        try:
            if len(args.filepaths) > 1:
                print(f"\nProcessing: {filepath}")
            rename_font_file(filepath, pattern=args.pattern, dry_run=args.dry_run, preserve_case=args.preserve_case)
            success_count += 1
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            error_count += 1
        except Exception as e:
            print(f"Error processing {filepath}: {e}", file=sys.stderr)
            error_count += 1
    # Print summary if multiple files were processed
    if len(args.filepaths) > 1:
        print(f"\n{'='*50}")
        print(f"Summary: {success_count} succeeded, {error_count} failed")
    raise SystemExit(0 if error_count == 0 else 1)
