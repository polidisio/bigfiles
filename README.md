<p align="center">
  <img src="https://img.icons8.com/color/96/000000/search--v1.png" alt="BigFiles Icon" width="80"/>
</p>

<h1 align="center">🔍 BigFiles</h1>

<p align="center">
  <strong>Interactive large file finder for macOS</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="Platform">
  <a href="https://github.com/polidisio/bigfiles-mac"><img src="https://img.shields.io/badge/macOS-App-blue.svg" alt="macOS App"></a>
</p>

> **Official macOS App available!** Download the native BigFiles app from the [bigfiles-mac](https://github.com/polidisio/bigfiles-mac) repository.

---

## ✨ Features

- 🚀 **Fast** - Async scanning with progress indicator
- 🎨 **Rich Output** - Colored tables with file icons and size bars
- 📊 **Size Bars** - Visual proportion bars showing relative file sizes
- 🔍 **Spotlight Filters** - Natural language filters like `type:video`, `larger:1GB`, `newer:30d`
- 📁 **Categories** - Group files by type (Videos, Photos, Audio, etc.)
- 🔔 **Notifications** - Get notified when scan completes
- 🎯 **Quick Actions** - Open, Reveal in Finder, QuickLook
- 💻 **Interactive TUI** - Full keyboard navigation (with `--interactive`)
- 🖥️ **Dark/Light Mode** - Adapts to your terminal theme
- 📤 **Export** - JSON or CSV output for further processing

## 📥 Installation

### 🏠 Homebrew (Recommended for macOS)

```bash
# Add the tap
brew tap polidisio/tap

# Install BigFiles
brew install bigfiles
```

To update:
```bash
brew upgrade bigfiles
```

### 📦 From Source

```bash
# Clone the repo
git clone https://github.com/polidisio/bigfiles.git
cd bigfiles

# Install dependencies
pip install rich click

# Run
python3 -m bigfiles.cli
```

### 🐍 pip

```bash
pip install bigfiles
```

### 🎮 Interactive Mode (Optional)

```bash
pip install bigfiles[interactive]
```

## 🎮 Usage

```bash
# Show help menu
bigfiles

# Scan your home directory (files > 100MB)
bigfiles

# Scan a specific directory
bigfiles -d ~/Downloads
bigfiles -d /Applications

# Files larger than 500MB
bigfiles -m 500

# Files between 100MB and 1GB
bigfiles -m 100 -M 1000

# Only PDFs and ZIPs
bigfiles -e pdf -e zip

# Only videos
bigfiles -e mp4 -e mov -e mkv

# Sort by modified date
bigfiles -s modified

# Top 20 largest files
bigfiles -l 20

# Exclude specific paths
bigfiles -x node_modules -x .git

# Simple list output
bigfiles -S -l 10
```

## 🔍 Spotlight Filters

Use natural language filters inspired by macOS Spotlight:

```bash
# Videos only
bigfiles -F "type:video"

# Files larger than 1GB
bigfiles -F "larger:1GB"

# Modified in last 30 days
bigfiles -F "newer:30d"

# Files containing 'backup'
bigfiles -F "name:backup"

# Combine filters
bigfiles -F "type:video" -F "larger:500MB"
```

## 📤 Export

```bash
# Output as JSON
bigfiles --output json

# Output as CSV
bigfiles --output csv

# Export to file
bigfiles --output json --export results.json

# Export to file
bigfiles --output csv --export results.csv
```

## 📁 Category Grouping

```bash
# Group files by category
bigfiles --group

# Shows totals like:
# 📹 Videos (23 files, 45.2 GB)
# 🖼️ Photos (156 files, 12.1 GB)
# 📄 Documents (89 files, 3.2 GB)
```

## 🔔 Notifications

```bash
# Get notified when scan completes
bigfiles --notify
```

## 🎯 Interactive TUI Mode

```bash
# Start interactive mode with keyboard navigation
bigfiles --interactive
```

**Keyboard shortcuts (TUI):**
- `↑/↓` or `j/k` - Navigate
- `Enter` or `o` - Open file
- `Space` - QuickLook preview
- `r` - Reveal in Finder
- `s` - Sort menu
- `f` - Filter menu
- `b` - Toggle size bars
- `g` - Toggle category grouping
- `n` - Toggle dark/light mode
- `h` - Help
- `q` - Quit

## 📋 All Options

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --dir` | Directory to scan | `~` |
| `-m, --min` | Minimum size (MB) | `100` |
| `-M, --max` | Maximum size (MB) | - |
| `-e, --ext` | Filter by extension(s) | - |
| `-x, --exclude` | Exclude paths containing pattern | - |
| `-s, --sort` | Sort by: size, name, path, modified | `size` |
| `-l, --limit` | Maximum results | `50` |
| `-S, --simple` | Simple list output | `false` |
| `-i, --interactive` | Interactive TUI mode | `false` |
| `--notify` | Send notification on completion | `false` |
| `-o, --output` | Output format: json, csv | - |
| `--export` | Export to file | - |
| `--group` | Group by category | `false` |
| `--no-bars` | Hide size bars | `false` |
| `--dark` | Force dark mode | - |
| `--light` | Force light mode | - |
| `-F, --filter` | Spotlight-style filter | - |

## 🔧 Requirements

- macOS (or Linux)
- Python 3.9+
- `rich` and `click` packages

## 📦 Uninstall

```bash
# Homebrew uninstall
brew uninstall bigfiles
brew untap polidisio/tap

# pip uninstall
pip uninstall bigfiles
```

## 🤝 Contributing

Contributions welcome! Please open an issue or PR at:
https://github.com/polidisio/bigfiles

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

<p align="center">
  Made with ❤️ and Python
</p>
