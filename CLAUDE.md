# CLAUDE.md - bigfiles

## Project Overview

**Name:** bigfiles  
**Type:** CLI Tool (Python)  
**Description:** Interactive CLI tool for finding large files on disk. Features async scanning with progress, colored output, filtering by size/extension, exclusion patterns, and multiple output formats.  
**Owner:** @polidisio  

## Tech Stack

- **Language:** Python 3.10+
- **Dependencies:** rich, click
- **Platform:** macOS/Linux
- **Build:** pyproject.toml

## Quick Start

```bash
# Homebrew (macOS)
brew install polidisio/tap/bigfiles

# pip
pip install bigfiles

# From source
pip install rich click
python3 -m bigfiles.cli

# Help
bigfiles --help
```

## File Structure

```
bigfiles/
├── bigfiles/              # Main package
│   └── cli.py             # CLI entry point
├── bin/                   # Binary/dist files
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Usage Examples

```bash
# Scan home directory (files > 100MB)
bigfiles

# Scan specific directory
bigfiles -d ~/Downloads

# Files larger than 500MB
bigfiles -m 500

# Files between 100MB and 1GB
bigfiles -m 100 -M 1000

# Only PDFs
bigfiles -e pdf

# Only videos
bigfiles -e mp4 -e mov -e mkv

# Top 20 largest
bigfiles -l 20

# Exclude paths
bigfiles -x node_modules -x .git

# Simple output
bigfiles -S -l 10
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --dir` | Directory to scan | ~ |
| `-m, --min` | Min size (MB) | 100 |
| `-M, --max` | Max size (MB) | - |
| `-e, --ext` | Filter by extension | - |
| `-x, --exclude` | Exclude paths | - |
| `-s, --sort` | Sort by | size |
| `-l, --limit` | Max results | 50 |
| `-S, --simple` | Simple list output | false |

## Auto-exclusions

- node_modules
- .git
- Caches

## Related Projects

- **[FindBigFiles](https://github.com/polidisio/filesizer)** - Native macOS app (SwiftUI)

## Resources

- Token optimization tips: shared/claude-optimization-tips.md (Obsidian Vault)

---

**Owner:** Jose Maudisio (@polidisio)  
**Last updated:** 2026-04-24

---

---

## Workflow

### Para tareas simples
Sé directo: "Añade validación al form" — no necesitas explicar contexto.

### Para tareas complejas (>3 pasos)
1. Agent propone plan primero
2. Usuario confirma
3. Agent ejecuta
4. Agent verifica con tests

### Para cada tarea
1. **Plan** → Si son >3 pasos, escribir en `tasks/todo.md`
2. **Verify** → Confirmar antes de cambios grandes
3. **Execute** → Cambio más pequeño posible
4. **Test** → Ejecutar tests, verificar regression
5. **Document** → Actualizar si es necesario

---

## Code Quality

### SIEMPRE
- Código legible y mantenible
- Seguir convenciones del proyecto
- DRY — no duplicar lógica
- Validar input antes de procesar

### NUNCA
- Hardcodear credenciales o tokens
- "Hacky fixes" sin justificación
- Duplicar código sin razón
- Commits sin mensaje descriptivo

---

## Security

- **NUNCA hardcodear** credenciales — usar environment variables
- **NUNCA exponer** tokens en logs o errores
- **Validar input** antes de procesar
- Si hay secrets, usar `.env` y nunca commitearlo

---

## Self-Improvement

### Si cometes un error
1. Documentar en `lessons.md` — qué salió mal, por qué, cómo evitarlo
2. Actualizar este archivo si la convención no estaba clara
3. No repetir

### Si descubres algo útil
- Documentar en notas del proyecto
- Compartir con Jose si es relevante

---

## Token Optimization

### Hacer
- Agrupar múltiples requests en uno
- Editar en vez de reply (menos historial)
- Nuevo tema = nueva conversación
- Planificar en chat, construir en workspace

### Evitar
- Subir carpetas enteras — solo archivos necesarios
- Múltiples prompts cortos seguidos
- Usar Opus para tareas simples
- Mantener contexto irrelevante

**Budget:** ~88% de tokens en conversaciones largas = solo historial. Mantenerlo limpio.

---

## Resources

**Obsidian Vault:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Saraiba/`

| Recurso | Ubicación en Vault |
|---------|---------------------|
| Best practices | `shared/coding-best-practices.md` |
| Optimization tips | `shared/claude-optimization-tips.md` |
| Skills docs | `shared/openclw-skills.md` |
| Guía coding agents | `shared/guia-coding-agents.md` |

---

## Contact

**Jose Maudisio** — @polidisio
**Issues:** Abrir en GitHub o preguntar en Telegram
