#!/usr/bin/env python3

import os
import sys
import re
import json
import argparse
from typing import List, Dict, Tuple, Any, Optional
import locale
import unicodedata
from pathlib import Path
from datetime import datetime


class FileMetadata:
    """Representation of a file's metadata with CJK support."""
    
    def __init__(self, path: str, size: float, language: str):
        """
        Initialize file metadata with Unicode normalization.
        
        Args:
            path: Relative path to the file
            size: File size in KB
            language: Detected programming language
        """
        # Normalize Unicode form for consistency
        self.path = unicodedata.normalize('NFC', path)
        self.size = size
        self.language = language
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "size": f"{self.size:.1f} KB",
            "language": self.language
        }


class RepoAnalyzer:
    """Analyzes repository content with full CJK support."""
    
    # Map file extensions to language names
    LANGUAGE_MAP = {
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
        '.cs': 'C#',
        '.fs': 'F#',
        '.clj': 'Clojure',
        '.groovy': 'Groovy',
        '.pl': 'Perl',
        '.hs': 'Haskell',
        '.jsx': 'React JSX',
        '.xml': 'XML',
        '.csv': 'CSV',
        '.ipynb': 'Jupyter Notebook',
    }
    
    # Binary file extensions to skip reading content
    BINARY_EXTENSIONS = {
        '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', 
        '.woff2', '.ttf', '.eot', '.otf', '.zip', '.tar', '.gz', '.rar',
        '.exe', '.dll', '.so', '.pyc', '.class', '.jar', '.war', '.iso', 
        '.bin', '.dat', '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.wav',
        '.flac', '.ogg', '.webm', '.webp', '.db', '.sqlite', '.mdb'
    }
    
    def __init__(self, repo_path: str, ignore_file_path: Optional[str] = None):
        """
        Initialize repository analyzer.
        
        Args:
            repo_path: Path to repository root
            ignore_file_path: Path to .gptignore file (optional)
        """
        self.repo_path = Path(unicodedata.normalize('NFC', repo_path))
        
        # Set default ignore file path if not provided
        if ignore_file_path is None:
            ignore_file_path = self.repo_path / ".gptignore"
            if not ignore_file_path.exists():
                ignore_file_path = Path(__file__).parent / ".gptignore"
        else:
            ignore_file_path = Path(unicodedata.normalize('NFC', ignore_file_path))
            
        self.ignore_list = self._get_ignore_list(ignore_file_path)
        
    def _get_ignore_list(self, ignore_file_path: Path) -> List[str]:
        """
        Read and return the list of patterns to ignore from .gptignore file.
        
        Args:
            ignore_file_path: Path to .gptignore file
            
        Returns:
            List of ignore patterns
        """
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
        
        # Add common files to ignore by default
        default_ignores = [
            '**/.git/**', '**/.svn/**', '**/.hg/**', '**/node_modules/**', 
            '**/__pycache__/**', '**/.vs/**', '**/.idea/**', '**/venv/**',
            '**/.env/**', '**/dist/**', '**/build/**', '**/coverage/**'
        ]
        
        for pattern in default_ignores:
            if pattern not in ignore_list:
                ignore_list.append(pattern)
                
        return ignore_list
        
    def _should_ignore(self, file_path: str) -> bool:
        """
        Check if a file should be ignored based on gitignore patterns.
        
        Args:
            file_path: The path to check, relative to repository root
        
        Returns:
            True if file should be ignored, False otherwise
        """
        # Normalize path for cross-platform compatibility
        normalized_path = unicodedata.normalize('NFC', file_path)
        if sys.platform == "win32":
            normalized_path = normalized_path.replace("\\", "/")
        
        # Also check against the path with trailing slash for directories
        paths_to_check = [normalized_path]
        if os.path.isdir(self.repo_path / normalized_path):
            paths_to_check.append(normalized_path + '/')
        
        # Track if path is explicitly negated
        negated = False
        
        for pattern in self.ignore_list:
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
            regex_pattern = self._convert_pattern_to_regex(pattern)
            
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
        
    def _convert_pattern_to_regex(self, pattern: str) -> str:
        """
        Convert a gitignore pattern to a regex pattern.
        
        Args:
            pattern: A gitignore pattern
            
        Returns:
            Equivalent regex pattern
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
        
    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected language name
        """
        # Normalize the path before splitting
        normalized_path = unicodedata.normalize('NFC', str(file_path)).lower()
        _, ext = os.path.splitext(normalized_path)
        return self.LANGUAGE_MAP.get(ext, 'Text')
        
    def _is_binary_file(self, file_path: str) -> bool:
        """
        Check if a file is binary based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is likely binary
        """
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.BINARY_EXTENSIONS
    
    def _generate_file_metadata(self, file_path: Path) -> FileMetadata:
        """
        Generate metadata for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileMetadata object
        """
        # Normalize paths before comparison
        normalized_file_path = unicodedata.normalize('NFC', str(file_path))
        normalized_repo_path = unicodedata.normalize('NFC', str(self.repo_path))
        
        # Use pathlib for relative path calculation
        rel_path = Path(normalized_file_path).relative_to(Path(normalized_repo_path))
        stats = os.stat(normalized_file_path)
        size_kb = stats.st_size / 1024
        
        return FileMetadata(
            path=str(rel_path).replace('\\', '/'),  # Always use forward slashes
            size=size_kb,
            language=self._detect_language(normalized_file_path)
        )
        
    def collect_repository_stats(self) -> Dict[str, Any]:
        """
        Collect comprehensive repository statistics.
        
        Returns:
            Dictionary of repository statistics
        """
        stats = {
            'total_files': 0,
            'total_size': 0.0,
            'file_count_by_type': {},
            'directory_structure': {},
            'languages': {},
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'largest_files': []
        }
        
        all_files = []
        
        # First collect all files
        for root, _, files in sorted(os.walk(self.repo_path)):
            for file in sorted(files):
                # Normalize file path
                file_path = Path(unicodedata.normalize('NFC', os.path.join(root, file)))
                rel_path = file_path.relative_to(self.repo_path)
                
                if not self._should_ignore(str(rel_path)):
                    try:
                        metadata = self._generate_file_metadata(file_path)
                        all_files.append((file_path, metadata))
                        
                        stats['total_files'] += 1
                        stats['total_size'] += metadata.size
                        
                        if metadata.language not in stats['languages']:
                            stats['languages'][metadata.language] = []
                        stats['languages'][metadata.language].append(metadata.path)
                        
                        ext = os.path.splitext(file)[1] or 'no_extension'
                        stats['file_count_by_type'][ext] = stats['file_count_by_type'].get(ext, 0) + 1
                    except Exception as e:
                        print(f"Warning: Error processing {file_path}: {str(e)}")
        
        # Sort languages by number of files
        stats['languages'] = {k: v for k, v in sorted(
            stats['languages'].items(), 
            key=lambda item: len(item[1]), 
            reverse=True
        )}
        
        # Get top 10 largest files
        stats['largest_files'] = sorted(
            [metadata.to_dict() for _, metadata in all_files],
            key=lambda x: float(x['size'].split()[0]),
            reverse=True
        )[:10]
        
        # Build directory structure
        for _, metadata in all_files:
            current_dict = stats['directory_structure']
            parts = metadata.path.split('/')
            for part in parts[:-1]:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            current_dict[parts[-1]] = {
                "size": f"{metadata.size:.1f} KB",
                "language": metadata.language,
            }
        
        return stats
        
    def process_repository_files(self, output_file, stats: Dict[str, Any]) -> None:
        """
        Process and write repository file contents.
        
        Args:
            output_file: Output file handle
            stats: Repository statistics dictionary
        """
        total_files = stats['total_files']
        processed_files = 0
        
        output_file.write("# File Contents\n\n")
        output_file.write("Each file section below contains:\n")
        output_file.write("1. File delimiter (=====)\n")
        output_file.write("2. File metadata (JSON format)\n")
        output_file.write("3. Content delimiter (-----)\n")
        output_file.write("4. File contents\n\n")
    
        for root, _, files in sorted(os.walk(self.repo_path)):
            for file in sorted(files):
                # Normalize file path
                file_path = Path(unicodedata.normalize('NFC', os.path.join(root, file)))
                rel_path = file_path.relative_to(self.repo_path)
    
                if not self._should_ignore(str(rel_path)):
                    try:
                        processed_files += 1
                        progress = (processed_files / total_files) * 100
                        print(f"Processing: [{processed_files}/{total_files}] {progress:.1f}% - {rel_path}", end='\r')
                        
                        metadata = self._generate_file_metadata(file_path)
                        
                        output_file.write("=" * 50 + "\n")
                        json.dump(metadata.to_dict(), output_file, indent=2, ensure_ascii=False)
                        output_file.write("\n" + "-" * 50 + "\n")
                        
                        # Skip content for binary files
                        if self._is_binary_file(str(file_path)):
                            output_file.write(f"[Binary file: content omitted]\n\n")
                            continue
                        
                        try:
                            # Try UTF-8 first
                            with open(file_path, 'r', encoding='utf-8') as f:
                                contents = f.read()
                        except UnicodeDecodeError:
                            try:
                                # Try with system default encoding
                                with open(file_path, 'r', encoding=locale.getpreferredencoding()) as f:
                                    contents = f.read()
                            except UnicodeDecodeError:
                                # If still fails, treat as binary
                                output_file.write(f"[Unable to read file content: encoding error]\n\n")
                                continue
                                
                        output_file.write(f"```{metadata.language.lower()}\n")
                        output_file.write(contents)
                        
                        # Ensure file ends with newline
                        if not contents.endswith('\n'):
                            output_file.write("\n")
                            
                        output_file.write("```\n\n")
                    except Exception as e:
                        print(f"Warning: Error processing {file_path}: {str(e)}")
        
        print("\nFile processing complete" + " " * 50)  # Clear progress line
                
    def write_repository_overview(self, output_file, stats: Dict[str, Any]) -> None:
        """
        Write comprehensive repository overview to output file.
        
        Args:
            output_file: Output file handle
            stats: Repository statistics dictionary
        """
        output_file.write("# Repository Overview\n\n")
        
        # Write analysis timestamp
        output_file.write(f"Analysis generated on: {stats['created_at']}\n\n")
        
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
        
        # Write file types sorted by count
        output_file.write("## File Types\n")
        output_file.write("```json\n")
        sorted_types = {k: v for k, v in sorted(
            stats['file_count_by_type'].items(), 
            key=lambda item: item[1], 
            reverse=True
        )}
        json.dump(sorted_types, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n```\n\n")
        
        # Write top 10 largest files
        output_file.write("## Largest Files\n")
        output_file.write("```json\n")
        json.dump(stats['largest_files'], output_file, indent=2, ensure_ascii=False)
        output_file.write("\n```\n\n")
        
        # Write files by language (sorted by file count)
        output_file.write("## Files by Language\n")
        output_file.write("```json\n")
        json.dump(stats['languages'], output_file, indent=2, ensure_ascii=False)
        output_file.write("\n```\n\n")
        
        # Write directory structure
        output_file.write("## Directory Structure\n")
        output_file.write("```json\n")
        json.dump(stats['directory_structure'], output_file, indent=2, ensure_ascii=False)
        output_file.write("\n```\n\n")


def main():
    """Main function to run the repository analyzer."""
    parser = argparse.ArgumentParser(
        description='Convert Git repository contents into text format optimized for AI language model processing.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('repo_path', type=str, help='Path to the repository')
    parser.add_argument('-p', '--preamble', type=str, help='Path to preamble file')
    parser.add_argument('-o', '--output', type=str, default='output.txt', help='Path to output file')
    parser.add_argument('-i', '--ignore', type=str, help='Path to custom .gptignore file')
    parser.add_argument('--skip-contents', action='store_true', help='Skip file contents, only include statistics')
    
    args = parser.parse_args()
    
    # Set the locale to system default for better CJK support
    locale.setlocale(locale.LC_ALL, '')
    
    try:
        # Initialize analyzer
        analyzer = RepoAnalyzer(
            repo_path=args.repo_path,
            ignore_file_path=args.ignore
        )
        
        # Collect repository statistics
        print("Collecting repository statistics...")
        repo_stats = analyzer.collect_repository_stats()
        
        # Write output file
        print(f"Writing output to {args.output}...")
        with open(args.output, 'w', encoding='utf-8') as output_file:
            # Write preamble if provided
            if args.preamble:
                with open(args.preamble, 'r', encoding='utf-8') as pf:
                    preamble_text = pf.read()
                    output_file.write(f"{preamble_text}\n\n")
            
            # Write repository overview
            analyzer.write_repository_overview(output_file, repo_stats)
            
            # Write file contents if not skipped
            if not args.skip_contents:
                analyzer.process_repository_files(output_file, repo_stats)
            
            output_file.write("\nEND_OF_FILE\n")
        
        print(f"Repository analysis complete!")
        print(f"Total files processed: {repo_stats['total_files']}")
        print(f"Total size: {repo_stats['total_size']:.1f} KB")
        print(f"Output written to: {args.output}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())