# Repository Content Converter

A Python tool that converts Git repository contents into a text format optimized for AI language model processing. The tool features robust CJK (Chinese, Japanese, Korean) character support and preserves both file structure and content while providing detailed analysis information.

## Key Features

- Full CJK character support through Unicode normalization
- File exclusion control via .gptignore
- Detailed repository statistics generation
- File contents output with metadata

## Installation

```bash
git clone https://github.com/kkensuke/repo_to_text.git
cd repo_to_text
```

This tool uses only Python standard library modules, so no additional package installation is required.

## Basic Usage

```bash
python3 repo_to_text_CJK.py /path/to/repository [-p /path/to/preamble.txt] [-o /path/to/output.txt]
```

### Options

- `-p`: Path to preamble file (optional)
- `-o`: Path to output file (default: output.txt)

## .gptignore Configuration

Use a `.gptignore` file to specify files and directories to exclude from conversion. The syntax is similar to .gitignore:

```plaintext
# Comments start with #
*.log
node_modules/
/dist
!important.log
```

Features:
- Lines starting with '#' are comments
- Supports glob patterns ('*', '?', etc.)
- Lines starting with '!' negate the pattern (include)
- Optional trailing slash '/' specifies directory-only matches
  - `node_modules/` matches only the directory
  - `node_modules` matches both directory and files

## Output Format

The output file is structured as follows:

1. Repository Overview
   ```markdown
   [Preamble]
   
   # Repository Overview
   
   ## General Statistics
   {total files, total size, language count}
   
   ## File Types
   {file count by extension}
   
   ## Directory Structure
   {JSON representation of directory structure}
   
   ## Files by Language
   {files listed by programming language}
   ```

2. File Contents
   ```markdown
   # File Contents
   
   ===================
   {
    "path": "relative/path/to/file",
    "size": "123.4 KB",
    "language": "Python"
   }
   -------------------
   ```{language}
   file contents
   ```

## Supported Languages

The tool automatically detects some programming languages which is included in the dictionary `extension_map` in `detect_language` function. You can add more languages to the dictionary if needed.

## Acknowledgments

This project is based on [gpt-repository-loader](https://github.com/original/gpt-repository-loader), with added CJK support and enhanced functionality.