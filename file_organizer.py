import os
import shutil
import time
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────────
#  COLOUR HELPERS
# ─────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    CYAN    = "\033[96m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"


# ─────────────────────────────────────────────
#  FILE TYPE CATEGORIES
# ─────────────────────────────────────────────
CATEGORIES = {
    "🖼  Images":     [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
                       ".webp", ".ico", ".tiff", ".raw", ".heic"],
    "📄 Documents":   [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf",
                       ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md"],
    "🎵 Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
                       ".m4a", ".opus"],
    "🎬 Videos":      [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
                       ".webm", ".m4v", ".mpeg"],
    "🗜  Archives":   [".zip", ".rar", ".tar", ".gz", ".7z", ".bz2",
                       ".xz", ".iso"],
    "💻 Code":        [".py", ".js", ".ts", ".html", ".css", ".java",
                       ".c", ".cpp", ".cs", ".php", ".rb", ".go",
                       ".rs", ".json", ".xml", ".yaml", ".yml", ".sh",
                       ".bat", ".sql"],
    "🔤 Fonts":       [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "⚙  Executables": [".exe", ".msi", ".dmg", ".apk", ".deb", ".rpm"],
    "📦 Others":      [],   # catch-all
}

# Build a flat reverse-lookup:  ".jpg" → "🖼  Images"
EXT_MAP = {}
for category, extensions in CATEGORIES.items():
    for ext in extensions:
        EXT_MAP[ext] = category


# ─────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────
def print_banner():
    print(f"""
{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════════╗
║        📂  FILE ORGANIZER                        ║
║        Synent Technologies Internship            ║
╚══════════════════════════════════════════════════╝
{C.RESET}""")


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_category(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    return EXT_MAP.get(ext, "📦 Others")


def safe_destination(dest_folder: Path, filename: str) -> Path:
    """If a file with the same name exists, append a number."""
    dest = dest_folder / filename
    if not dest.exists():
        return dest
    stem   = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        dest = dest_folder / new_name
        if not dest.exists():
            return dest
        counter += 1


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ─────────────────────────────────────────────
#  SCAN — preview what will be moved
# ─────────────────────────────────────────────
def scan_directory(target: Path) -> dict:
    """
    Returns a dict:  category → list of Path objects
    Only considers FILES directly inside target (non-recursive by default).
    Skips the organizer script itself.
    """
    plan = {cat: [] for cat in CATEGORIES}
    script_name = Path(__file__).name

    for item in sorted(target.iterdir()):
        if item.is_dir():
            continue
        if item.name == script_name:
            continue
        if item.name.startswith("."):
            continue
        cat = get_category(item)
        plan[cat].append(item)

    return plan


# ─────────────────────────────────────────────
#  PREVIEW TABLE
# ─────────────────────────────────────────────
def show_preview(plan: dict):
    total = sum(len(v) for v in plan.values())
    if total == 0:
        print(f"\n  {C.YELLOW}⚠  No files found to organise.{C.RESET}\n")
        return False

    print(f"\n{C.BOLD}  📋 Preview — {total} file(s) will be organised:{C.RESET}\n")
    print(f"  {C.DIM}{'Category':<22} {'Files':>6}   {'File names'}{C.RESET}")
    print(f"  {'─'*60}")

    for cat, files in plan.items():
        if not files:
            continue
        names = ", ".join(f.name for f in files[:3])
        if len(files) > 3:
            names += f"  {C.DIM}+{len(files)-3} more{C.RESET}"
        print(f"  {C.CYAN}{cat:<22}{C.RESET}  {C.BOLD}{len(files):>4}{C.RESET}   {names}")

    print(f"  {'─'*60}")
    print(f"  {C.GREEN}{C.BOLD}  Total: {total} files{C.RESET}\n")
    return True


# ─────────────────────────────────────────────
#  ORGANISE — actually move files
# ─────────────────────────────────────────────
def organise(target: Path, plan: dict, log: list):
    moved   = 0
    skipped = 0

    for cat, files in plan.items():
        if not files:
            continue

        # Folder name = clean label without emoji prefix spaces
        folder_name = cat.strip()
        dest_folder = target / folder_name
        dest_folder.mkdir(exist_ok=True)

        for file in files:
            try:
                dest = safe_destination(dest_folder, file.name)
                size = file.stat().st_size
                shutil.move(str(file), str(dest))

                log.append({
                    "file":     file.name,
                    "category": cat,
                    "size":     size,
                    "status":   "Moved",
                })
                print(f"  {C.GREEN}✔{C.RESET}  {file.name:<35} → {C.CYAN}{folder_name}{C.RESET}")
                moved += 1

            except Exception as e:
                log.append({
                    "file":     file.name,
                    "category": cat,
                    "size":     0,
                    "status":   f"Error: {e}",
                })
                print(f"  {C.RED}✘{C.RESET}  {file.name:<35}  {C.RED}Error: {e}{C.RESET}")
                skipped += 1

    return moved, skipped


# ─────────────────────────────────────────────
#  SAVE LOG
# ─────────────────────────────────────────────
def save_log(target: Path, log: list, moved: int, skipped: int):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path  = target / "organizer_log.txt"

    with open(log_path, "w") as f:
        f.write("File Organizer — Activity Log\n")
        f.write(f"Run at   : {timestamp}\n")
        f.write(f"Directory: {target}\n")
        f.write(f"Moved    : {moved}  |  Skipped/Errors: {skipped}\n")
        f.write("=" * 55 + "\n\n")
        for entry in log:
            size_str = format_size(entry["size"]) if entry["size"] else "—"
            f.write(f"[{entry['status']:<6}]  {entry['file']:<35}  {entry['category']:<22}  {size_str}\n")

    print(f"\n  {C.GREEN}✔  Log saved → {C.BOLD}organizer_log.txt{C.RESET}")


# ─────────────────────────────────────────────
#  UNDO — move files back to root
# ─────────────────────────────────────────────
def undo_organisation(target: Path):
    print(f"\n  {C.YELLOW}↩  Undoing organisation...{C.RESET}\n")
    restored = 0

    for cat in CATEGORIES:
        folder = target / cat.strip()
        if not folder.is_dir():
            continue
        for file in folder.iterdir():
            if file.is_file():
                dest = safe_destination(target, file.name)
                shutil.move(str(file), str(dest))
                print(f"  {C.CYAN}↩{C.RESET}  {file.name}")
                restored += 1
        # Remove folder if now empty
        try:
            folder.rmdir()
        except OSError:
            pass

    print(f"\n  {C.GREEN}✔  {restored} file(s) restored to root.{C.RESET}\n")


# ─────────────────────────────────────────────
#  INPUT HELPERS
# ─────────────────────────────────────────────
def ask_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        ans = input(f"  {prompt} {C.DIM}{hint}{C.RESET}: ").strip().lower()
        if ans == "":    return default
        if ans in ("y", "yes"): return True
        if ans in ("n", "no"):  return False
        print(f"  {C.YELLOW}⚠  Enter y or n.{C.RESET}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    import sys
    if sys.platform == "win32":
        os.system("color")

    print_banner()

    # ── Choose mode ──────────────────────────
    print(f"{C.BOLD}  Choose mode:{C.RESET}")
    print(f"  {C.CYAN}1{C.RESET}  Organise a folder")
    print(f"  {C.CYAN}2{C.RESET}  Undo organisation (restore files)")
    print(f"  {C.CYAN}3{C.RESET}  Exit\n")

    while True:
        choice = input(f"  Enter choice {C.DIM}[1/2/3]{C.RESET}: ").strip()
        if choice in ("1", "2", "3"):
            break
        print(f"  {C.YELLOW}⚠  Enter 1, 2, or 3.{C.RESET}")

    if choice == "3":
        print(f"\n  {C.GREEN}Goodbye!{C.RESET}\n")
        return

    # ── Get target directory ─────────────────
    print(f"\n  {C.DIM}Press Enter to use the current directory, or type a path.{C.RESET}")
    raw = input(f"  Target folder path: ").strip()
    target = Path(raw) if raw else Path.cwd()

    if not target.exists() or not target.is_dir():
        print(f"\n  {C.RED}✘  Directory not found: {target}{C.RESET}\n")
        return

    print(f"\n  {C.CYAN}📁 Target:{C.RESET} {C.BOLD}{target}{C.RESET}")

    # ── UNDO mode ────────────────────────────
    if choice == "2":
        undo_organisation(target)
        return

    # ── ORGANISE mode ────────────────────────
    print(f"\n  {C.DIM}Scanning...{C.RESET}")
    plan = scan_directory(target)

    has_files = show_preview(plan)
    if not has_files:
        return

    confirm = ask_yes_no("Proceed with organisation", True)
    if not confirm:
        print(f"\n  {C.YELLOW}Cancelled.{C.RESET}\n")
        return

    print(f"\n{C.CYAN}{'─'*52}{C.RESET}")
    print(f"{C.BOLD}  🚀 Moving files...{C.RESET}\n")

    log = []
    start = time.time()
    moved, skipped = organise(target, plan, log)
    elapsed = time.time() - start

    # ── Summary ──────────────────────────────
    print(f"\n{C.CYAN}{'─'*52}{C.RESET}")
    print(f"{C.BOLD}  ✅ Done in {elapsed:.2f}s{C.RESET}")
    print(f"  {C.GREEN}Moved  : {moved}{C.RESET}")
    if skipped:
        print(f"  {C.RED}Errors : {skipped}{C.RESET}")

    if ask_yes_no("\n  Save activity log", True):
        save_log(target, log, moved, skipped)

    print(f"\n{C.GREEN}{C.BOLD}  📂 Folder organised successfully!{C.RESET}\n")


if __name__ == "__main__":
    main()
