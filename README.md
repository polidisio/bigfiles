<p align="center">
  <img src="https://img.icons8.com/color/96/000000/search--v1.png" alt="BigFiles Icon" width="80"/>
</p>

<h1 align="center">🔍 BigFiles</h1>

<p align="center">
  <strong>Interactive large file finder for macOS</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="Platform">
</p>

---

## ✨ Features

- 🚀 **Fast** - Async scanning with progress indicator
- 🎨 **Rich Output** - Colored tables with file icons
- 📊 **Sort** by size, name, path, or modified date
- 🔍 **Filters** - Size range, extensions, exclude patterns
- 📁 **Auto-excludes** common folders like `node_modules`, `.git`, `Caches`

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

## 🔧 Requirements

- macOS (or Linux)
- Python 3.10+
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
