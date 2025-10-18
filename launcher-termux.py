import curses
import os
import subprocess

# 🔹 Caminho base onde procurar arquivos de código
CODE_DIR = os.path.expanduser("~")

def get_termux_commands():
    """Lista comandos executáveis do Termux."""
    paths = os.getenv("PATH", "").split(":")
    cmds = set()
    for path in paths:
        if os.path.isdir(path):
            for f in os.listdir(path):
                full = os.path.join(path, f)
                if os.access(full, os.X_OK) and not os.path.isdir(full):
                    cmds.add(f)
    return sorted(cmds)

def get_android_apps():
    """Lista pacotes Android (pode precisar de permissão)."""
    try:
        output = subprocess.check_output(["pm", "list", "packages"], text=True)
        return sorted([line.replace("package:", "").strip() for line in output.splitlines()])
    except Exception:
        return []

def get_code_files():
    """Lista arquivos de código na pasta CODE_DIR."""
    exts = (".py", ".rb", ".c", ".cpp", ".sh")
    code_files = []
    for root, _, files in os.walk(CODE_DIR):
        for f in files:
            if f.endswith(exts):
                code_files.append(os.path.join(root, f))
    return sorted(code_files)

def launch_termux_cmd(cmd):
    subprocess.Popen([cmd], start_new_session=True)

def launch_android_app(package):
    try:
        subprocess.run(["am", "start", "-n", f"{package}/.MainActivity"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        subprocess.run(["am", "start", "-a", "android.intent.action.MAIN", "-n", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_code_file(filepath):
    """Executa arquivos de código conforme a extensão."""
    ext = os.path.splitext(filepath)[1]
    if ext == ".py":
        cmd = ["python3", filepath]
    elif ext == ".rb":
        cmd = ["ruby", filepath]
    elif ext == ".sh":
        cmd = ["bash", filepath]
    elif ext in (".c", ".cpp"):
        exe = "/tmp/a.out"
        compiler = "gcc" if ext == ".c" else "g++"
        subprocess.run([compiler, filepath, "-o", exe])
        cmd = [exe]
    else:
        return
    subprocess.run(cmd)

def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        stdscr.addstr(y, x, text[:w - x - 1], attr)

def draw_box(stdscr, h, w, title, color_pair):
    stdscr.attron(curses.color_pair(color_pair))
    safe_addstr(stdscr, 0, 0, "+" + "-" * (w - 2) + "+")
    for i in range(1, h - 1):
        safe_addstr(stdscr, i, 0, "|" + " " * (w - 2) + "|")
    safe_addstr(stdscr, h - 1, 0, "+" + "-" * (w - 2) + "+")
    safe_addstr(stdscr, 0, max(1, (w - len(title)) // 2), title)
    stdscr.attroff(curses.color_pair(color_pair))

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)

    mode = 0  # 0 = Termux, 1 = Android, 2 = Code
    data = [get_termux_commands(), get_android_apps(), get_code_files()]
    labels = ["🧰 Termux Commands", "📱 Android Apps", "💾 Code Files"]

    search = ""
    pos = 0
    scroll = 0
    focus_search = False

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        draw_box(stdscr, h, w, f" {labels[mode]} ", 1)
        safe_addstr(stdscr, 1, 2, f"Search: {search}", curses.color_pair(2))
        filtered = [c for c in data[mode] if search.lower() in c.lower()]
        visible_h = h - 6

        for i in range(scroll, min(len(filtered), scroll + visible_h)):
            y = 2 + (i - scroll)
            item = filtered[i]
            color = curses.color_pair(4 if mode != 2 else 6)
            if i == pos:
                safe_addstr(stdscr, y, 2, f"> {item[:w-4]}", curses.color_pair(3))
            else:
                safe_addstr(stdscr, y, 4, item[:w - 6], color)

        if not filtered:
            safe_addstr(stdscr, 3, max(1, (w - 25)//2), "Nenhum item encontrado", curses.color_pair(5))

        footer = f" ↑↓ mover | Enter abrir | / buscar | ←→ trocar | q sair "
        safe_addstr(stdscr, h - 1, max(1, (w - len(footer)) // 2), footer, curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord('q'), 27):
            break
        elif key == ord('/'):
            focus_search = True
            search = ""
        elif key == curses.KEY_RIGHT:
            mode = (mode + 1) % 3
            pos = scroll = 0
            search = ""
            if mode == 1 and not data[1]:
                data[1] = get_android_apps()
            elif mode == 2 and not data[2]:
                data[2] = get_code_files()
        elif key == curses.KEY_LEFT:
            mode = (mode - 1) % 3
            pos = scroll = 0
            search = ""
        elif focus_search:
            if key in (10, 13):
                focus_search = False
            elif key in (8, 127):
                search = search[:-1]
            elif 32 <= key <= 126:
                search += chr(key)
        elif key == curses.KEY_UP:
            if pos > 0:
                pos -= 1
                if pos < scroll:
                    scroll -= 1
        elif key == curses.KEY_DOWN:
            if pos < len(filtered) - 1:
                pos += 1
                if pos >= scroll + visible_h:
                    scroll += 1
        elif key in (10, 13):
            if filtered:
                curses.endwin()
                if mode == 0:
                    launch_termux_cmd(filtered[pos])
                elif mode == 1:
                    launch_android_app(filtered[pos])
                elif mode == 2:
                    run_code_file(filtered[pos])
                input("\nPressione Enter para voltar...")
                stdscr = curses.initscr()
                curses.curs_set(0)
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_CYAN, -1)
                curses.init_pair(2, curses.COLOR_WHITE, -1)
                curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
                curses.init_pair(4, curses.COLOR_GREEN, -1)
                curses.init_pair(5, curses.COLOR_YELLOW, -1)
                curses.init_pair(6, curses.COLOR_MAGENTA, -1)

if __name__ == "__main__":
    curses.wrapper(main)
