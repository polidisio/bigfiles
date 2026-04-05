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
- 📊 **Sort** by size, name, or path
- 🔍 **Filters** - Customizable minimum size
- 📁 **Auto-excludes** common folders like `node_modules`, `.git`, `Caches`

## 📥 Installation

### From source

```bash
# Clone the repo
git clone https://github.com/polidisio/bigfiles.git
cd bigfiles

# Install dependencies
pip install rich click

# Run
python3 -m bigfiles.cli
```

### With pip

```bash
pip install bigfiles
```

## 🎮 Usage

```bash
# Scan home directory with default minimum (100MB)
bigfiles

# Scan specific directory
bigfiles -d ~/Downloads
bigfiles --dir /Applications

# Change minimum size
bigfiles -m 500        # > 500 MB
bigfiles --min 1       # > 1 MB

# Sort by name
bigfiles -s name

# Limit results
bigfiles -l 20

# Simple list mode (no formatting)
bigfiles -L
```

## 📸 Screenshots

```
┌─────────────────────────────────────────────┐
│  🔍 BIGFILES - Large File Finder            │
├─────────────────────────────────────────────┤
│  Directory: ~/                             │
│  Minimum: 100 MB                           │
├─────────────────────────────────────────────┤
│  1. 📱 Projects/CardSurvivor.xc   4.2 GB   │
│  2. 🎬 Videos/vacations.mov      2.8 GB   │
│  3. 📦 Parallels/win10.vm         1.5 GB  │
│  4. 💿 Images/backup.dmg          890 MB   │
│  5. 🗄️  Databases/dump.sql         756 MB  │
└─────────────────────────────────────────────┘
```

## 🛠️ Requirements

- Python 3.10+
- macOS (or any Unix system)
- rich >= 13.0.0
- click >= 8.0.0

## 📝 Roadmap

- [ ] Full interactive TUI mode (arrow navigation)
- [ ] Delete files directly from the app
- [ ] Scan history
- [ ] Export to CSV/JSON
- [ ] Finder comments support

## 🤝 Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📜 License

MIT License - see [LICENSE](LICENSE)

## 👤 Author

**Jose M.** - [polidisio](https://github.com/polidisio)

---

<p align="center">
  Made with ❤️ and Python
</p>
