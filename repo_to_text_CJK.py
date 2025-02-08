#!/usr/bin/env python3

import os
import sys
import re
import json
from typing import List, Dict
import locale
import unicodedata

class FileMetadata:
    def __init__(self, path: str, size: float, language: str):
        # Normalize Unicode form for consistency
        self.path = unicodedata.normalize('NFC', path)
        self.size = size
        self.language = language
        
    def to_dict(self):
        return {
            "path": self.path,
            "size": f"{self.size:.1f} KB",
            "language": self.language
        }

def detect_language(file_path: str) -> str:
    """Detect programming language based on file extension."""
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.cpp': 'C++',
        '.hpp': 'C++ Header',
        '.html': 'HTML',
        '.css': 'CSS',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.sh': 'Shell',
        '.bat': 'Batch',
        '.ps1': 'PowerShell',
        '.sql': 'SQL',
        '.r': 'R',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.jsx': 'JSX',
        '.tsx': 'TSX',
        '.vue': 'Vue',
        '.scala': 'Scala',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.tex': 'TeX',
        '.ex': 'Elixir',
        '.erl': 'Erlang',
    }
    # Normalize the path before splitting
    normalized_path = unicodedata.normalize('NFC', file_path.lower())
    _, ext = os.path.splitext(normalized_path)
    return extension_map.get(ext, 'Text')

def get_ignore_list(ignore_file_path: str) -> List[str]:
    """Read and return the list of patterns to ignore from .gptignore file."""
    ignore_list = []
    try:
        with open(ignore_file_path, 'r', encoding='utf-8') as ignore_file:
            for line in ignore_file:
                # Strip whitespace and normalize
                line = line.strip()
                line = unicodedata.normalize('NFC', line)
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Handle Windows path separators
                if sys.platform == "win32":
                    line = line.replace("\\", "/")
                
                # Add pattern to ignore list
                ignore_list.append(line)
    except FileNotFoundError:
        print(f"Warning: Ignore file not found at {ignore_file_path}")
    except UnicodeDecodeError:
        print(f"Warning: Unable to read ignore file with UTF-8 encoding: {ignore_file_path}")
        # Fallback to system default encoding
        with open(ignore_file_path, 'r', encoding=locale.getpreferredencoding()) as ignore_file:
            for line in ignore_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    line = unicodedata.normalize('NFC', line)
                    if sys.platform == "win32":
                        line = line.replace("\\", "/")
                    ignore_list.append(line)
    return ignore_list

def should_ignore(file_path: str, ignore_list: List[str]) -> bool:
    """
    Check if a file should be ignored based on gitignore patterns.
    
    Args:
        file_path: The path to check, relative to repository root
        ignore_list: List of ignore patterns from .gptignore file
    
    Returns:
        bool: True if file should be ignored, False otherwise
    """
    # Normalize path for cross-platform compatibility
    normalized_path = unicodedata.normalize('NFC', file_path)
    if sys.platform == "win32":
        normalized_path = normalized_path.replace("\\", "/")
    
    # Also check against the path with trailing slash for directories
    paths_to_check = [normalized_path]
    if os.path.isdir(file_path):
        paths_to_check.append(normalized_path + '/')
    
    # Track if path is explicitly negated
    negated = False
    
    for pattern in ignore_list:
        # Normalize pattern
        pattern = unicodedata.normalize('NFC', pattern)
        if sys.platform == "win32":
            pattern = pattern.replace("\\", "/")
        
        # Handle empty lines and comments
        if not pattern or pattern.startswith('#'):
            continue
            
        # Handle negation patterns
        is_negated_pattern = pattern.startswith('!')
        if is_negated_pattern:
            pattern = pattern[1:]
        
        # Convert pattern to regex
        regex_pattern = _convert_pattern_to_regex(pattern)
        
        # Check both the regular path and path-with-slash against the pattern
        matched = any(re.match(regex_pattern, path) for path in paths_to_check)
        
        if matched:
            if is_negated_pattern:
                negated = True
            else:
                # Only ignore if path hasn't been negated
                if not negated:
                    return True
    
    # Return False if path was negated, or if no patterns matched
    return False

def _convert_pattern_to_regex(pattern: str) -> str:
    """
    Convert a gitignore pattern to a regex pattern.
    
    Args:
        pattern: A gitignore pattern
        
    Returns:
        str: Equivalent regex pattern
    """
    if not pattern:
        return "^$"
        
    # Remove leading and trailing whitespace
    pattern = pattern.strip()
    
    # Handle directory-specific patterns
    is_dir_only = pattern.endswith('/')
    if is_dir_only:
        pattern = pattern[:-1]
    
    # Start with beginning of string
    regex = '^'
    
    # Handle leading slashes
    if pattern.startswith('/'):
        pattern = pattern[1:]
    else:
        regex = regex + '(?:.+/)?'
    
    # Convert glob patterns to regex
    i = 0
    while i < len(pattern):
        if pattern[i] == '*':
            if i + 1 < len(pattern) and pattern[i + 1] == '*':
                # ** matches zero or more directories
                regex += '.*'
                i += 2
            else:
                # * matches anything except /
                regex += '[^/]*'
                i += 1
        elif pattern[i] == '?':
            # ? matches any single character except /
            regex += '[^/]'
            i += 1
        elif pattern[i] == '[':
            # Character classes
            j = i + 1
            while j < len(pattern) and pattern[j] != ']':
                j += 1
            if j < len(pattern):
                regex += '[' + pattern[i+1:j] + ']'
                i = j + 1
            else:
                regex += '\\['
                i += 1
        else:
            # Escape special regex characters
            if pattern[i] in '.+(){}\\^$|':
                regex += '\\'
            regex += pattern[i]
            i += 1
    
    # End of pattern
    if is_dir_only:
        regex += '(?:/|$)'
    else:
        # Allow matching both files and directories
        regex += '(?:/.*)?$'
    
    return regex

def generate_file_metadata(file_path: str, repo_path: str) -> FileMetadata:
    """Generate metadata for a file."""
    # Normalize paths before comparison
    normalized_file_path = unicodedata.normalize('NFC', file_path)
    normalized_repo_path = unicodedata.normalize('NFC', repo_path)
    relative_path = os.path.relpath(normalized_file_path, normalized_repo_path)
    stats = os.stat(normalized_file_path)
    size_kb = stats.st_size / 1024
    return FileMetadata(
        path=relative_path,
        size=size_kb,
        language=detect_language(normalized_file_path)
    )

def collect_repository_stats(repo_path: str, ignore_list: List[str]) -> Dict:
    """First pass: Collect repository statistics without writing files."""
    stats = {
        'total_files': 0,
        'total_size': 0.0,
        'file_count_by_type': {},
        'directory_structure': {},
        'languages': {}
    }
    
    for root, _, files in sorted(os.walk(repo_path)):
        for file in sorted(files):
            # Normalize file path
            file_path = unicodedata.normalize('NFC', os.path.join(root, file))
            relative_file_path = os.path.relpath(file_path, repo_path)
            
            if not should_ignore(relative_file_path, ignore_list):
                try:
                    metadata = generate_file_metadata(file_path, repo_path)
                    
                    stats['total_files'] += 1
                    stats['total_size'] += metadata.size
                    
                    if metadata.language not in stats['languages']:
                        stats['languages'][metadata.language] = []
                    stats['languages'][metadata.language].append(metadata.path)
                    
                    ext = os.path.splitext(file)[1] or 'no_extension'
                    stats['file_count_by_type'][ext] = stats['file_count_by_type'].get(ext, 0) + 1
                    
                    current_dict = stats['directory_structure']
                    parts = metadata.path.split(os.sep)
                    for part in parts[:-1]:
                        if part not in current_dict:
                            current_dict[part] = {}
                        current_dict = current_dict[part]
                    current_dict[parts[-1]] = {
                        "size": f"{metadata.size:.1f} KB",
                        "language": metadata.language,
                    }
                    
                except Exception as e:
                    print(f"Warning: Error processing {file_path}: {str(e)}")
    
    return stats

def process_repository_files(repo_path: str, ignore_list: List[str], output_file) -> None:
    """Second pass: Write file contents with metadata."""
    output_file.write("# File Contents\n\n")
    output_file.write("Each file section below contains:\n")
    output_file.write("1. File delimiter (=====)\n")
    output_file.write("2. File metadata (JSON format)\n")
    output_file.write("3. Content delimiter (-----)\n")
    output_file.write("4. File contents\n")
    output_file.write("5. End marker (END_OF_FILE) at the end of this file\n\n")

    for root, _, files in sorted(os.walk(repo_path)):
        for file in sorted(files):
            # Normalize file path
            file_path = unicodedata.normalize('NFC', os.path.join(root, file))
            relative_file_path = os.path.relpath(file_path, repo_path)

            if not should_ignore(relative_file_path, ignore_list):
                try:
                    metadata = generate_file_metadata(file_path, repo_path)
                    
                    output_file.write("=" * 50 + "\n")
                    json.dump(metadata.to_dict(), output_file, indent=2, ensure_ascii=False)
                    output_file.write("\n" + "-" * 50 + "\n")
                    
                    try:
                        # Try UTF-8 first
                        with open(file_path, 'r', encoding='utf-8') as f:
                            contents = f.read()
                    except UnicodeDecodeError:
                        # Fallback to system default encoding
                        with open(file_path, 'r', encoding=locale.getpreferredencoding()) as f:
                            contents = f.read()
                            
                    output_file.write(f"```{metadata.language.lower()}\n")
                    output_file.write(contents)
                    output_file.write("\n```")
                    output_file.write("\n\n")
                except Exception as e:
                    print(f"Warning: Error processing {file_path}: {str(e)}")

def write_repository_overview(stats: Dict, output_file) -> None:
    """Write comprehensive repository overview at the beginning of the file."""
    output_file.write("# Repository Overview\n\n")
    
    # Write general statistics
    output_file.write("## General Statistics\n")
    output_file.write("```json\n")
    general_stats = {
        "total_files": stats['total_files'],
        "total_size": f"{stats['total_size']:.1f} KB",
        "language_count": len(stats['languages'])
    }
    json.dump(general_stats, output_file, indent=2, ensure_ascii=False)
    output_file.write("\n```\n\n")
    
    # Write file types
    output_file.write("## File Types\n")
    output_file.write("```json\n")
    json.dump(stats['file_count_by_type'], output_file, indent=2, ensure_ascii=False)
    output_file.write("\n```\n\n")
    
    # Write directory structure
    output_file.write("## Directory Structure\n")
    output_file.write("```json\n")
    json.dump(stats['directory_structure'], output_file, indent=2, ensure_ascii=False)
    output_file.write("\n```\n\n")
    
    # Write files by language
    output_file.write("## Files by Language\n")
    output_file.write("```json\n")
    json.dump(stats['languages'], output_file, indent=2, ensure_ascii=False)
    output_file.write("\n```\n\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python git_to_text.py /path/to/git/repository [-p /path/to/preamble.txt] [-o /path/to/output_file.txt]")
        sys.exit(1)

    # Set the locale to system default for better CJK support
    locale.setlocale(locale.LC_ALL, '')

    repo_path = unicodedata.normalize('NFC', sys.argv[1])
    ignore_file_path = os.path.join(repo_path, ".gptignore")
    if sys.platform == "win32":
        ignore_file_path = ignore_file_path.replace("/", "\\")

    if not os.path.exists(ignore_file_path):
        HERE = os.path.dirname(os.path.abspath(__file__))
        ignore_file_path = os.path.join(HERE, ".gptignore")

    preamble_file = None
    if "-p" in sys.argv:
        preamble_file = unicodedata.normalize('NFC', sys.argv[sys.argv.index("-p") + 1])

    output_file_path = 'output.txt'
    if "-o" in sys.argv:
        output_file_path = unicodedata.normalize('NFC', sys.argv[sys.argv.index("-o") + 1])

    ignore_list = get_ignore_list(ignore_file_path)
    repo_stats = collect_repository_stats(repo_path, ignore_list)

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        if preamble_file:
            with open(preamble_file, 'r', encoding='utf-8') as pf:
                preamble_text = pf.read()
                output_file.write(f"{preamble_text}\n\n")
        
        write_repository_overview(repo_stats, output_file)
        process_repository_files(repo_path, ignore_list, output_file)
        output_file.write("\nEND_OF_FILE\n")

    print(f"Repository contents written to {output_file_path}")
    print(f"Total files processed: {repo_stats['total_files']}")
    print(f"Total size: {repo_stats['total_size']:.1f} KB")

if __name__ == "__main__":
    main()