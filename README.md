<p align="center">
  <img src="https://img.icons8.com/color/96/000000/search--v1.png" alt="BigFiles Icon" width="80"/>
</p>

<h1 align="center">🔍 BigFiles</h1>

<p align="center">
  <strong>Buscador interactivo de archivos grandes para macOS</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="Platform">
</p>

---

## ✨ Características

- 🚀 **Rápido** - Escaneo asíncrono con tqdm
- 🎨 **Salida Rich** - Tablas coloreadas con iconos
- 📊 **Ordena** por tamaño, nombre o ruta
- 🔍 **Filtros** - Tamaño mínimo personalizable
- 📁 **Excluye** automáticamente carpetas como `node_modules`, `.git`, `Caches`

## 📥 Instalación

### Desde código fuente

```bash
# Clonar el repo
git clone https://github.com/polidisio/bigfiles.git
cd bigfiles

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -e .

# Ejecutar
bigfiles
```

### Con pip

```bash
pip install bigfiles
```

## 🎮 Uso

```bash
# Escanea tu home con el mínimo por defecto (100MB)
bigfiles

# Escanea un directorio específico
bigfiles -d ~/Downloads
bigfiles --dir /Applications

# Cambiar tamaño mínimo
bigfiles -m 500        # > 500 MB
bigfiles --min 1       # > 1 MB

# Ordenar por nombre
bigfiles -s name

# Limitar resultados
bigfiles -l 20

# Modo lista simple (sin formato)
bigfiles -L
```

## 📸 Screenshots

```
┌─────────────────────────────────────────────┐
│  🔍 BIGFILES - Buscador de archivos grandes │
├─────────────────────────────────────────────┤
│  Directorio: ~/                             │
│  Mínimo: 100 MB                             │
├─────────────────────────────────────────────┤
│  1. 📱 Projects/CardSurvivor.xc   4.2 GB   │
│  2. 🎬 Videos/vacaciones.mov      2.8 GB   │
│  3. 📦 Parallels/win10.vm         1.5 GB   │
│  4. 💿 Images/backup.dmg          890 MB  │
│  5. 🗄️  Databases/dump.sql         756 MB  │
└─────────────────────────────────────────────┘
```

## 🛠️ Requisitos

- Python 3.10+
- macOS (或其他 Unix 系统)
- rich >= 13.0.0
- click >= 8.0.0
- textual >= 0.50.0 (opcional)

## 📝 Roadmap

- [ ] Modo TUI interactivo completo (navegación con flechas)
- [ ] Eliminar archivos directamente desde la app
- [ ] Historial de escaneos
- [ ] Exportar a CSV/JSON
- [ ] Soporte para Finder comments

## 🤝 Contribuir

1. Fork el repo
2. Crea una rama (`git checkout -b feature/nueva-feature`)
3. Commit tus cambios (`git commit -m 'Add nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

## 📜 Licencia

MIT License - ver archivo [LICENSE](LICENSE)

## 👤 Autor

**Jose M.** - [polidisio](https://github.com/polidisio)

---

<p align="center">
  Hecho con ❤️ y Python
</p>
