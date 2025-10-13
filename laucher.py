import curses
import os
import subprocess
import configparser
import sys

def get_installed_apps():
    paths = ['/usr/share/applications/', os.path.expanduser('~/.local/share/applications/')]
    apps = []
    for path in paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.desktop'):
                    full_path = os.path.join(path, file)
                    try:
                        config = configparser.ConfigParser()
                        config.optionxform = str
                        config.read(full_path, encoding='utf-8')
                        if 'Desktop Entry' in config:
                            entry = config['Desktop Entry']
                            if 'Name' in entry and 'Exec' in entry:
                                name = entry['Name']
                                exec_cmd = entry['Exec']
                                if 'NoDisplay' not in entry or entry['NoDisplay'].lower() != 'true':
                                    apps.append((name, exec_cmd))
                    except Exception:
                        continue
    apps = list(set(apps))
    apps.sort(key=lambda x: x[0].lower())
    return apps

def launch_app(exec_cmd):
    try:
        exec_cmd = exec_cmd.split('%')[0].strip()
        if exec_cmd:
            subprocess.Popen(exec_cmd, shell=True, start_new_session=True)
    except Exception:
        pass

def draw_border(stdscr, height, width):
    try:
        stdscr.attron(curses.color_pair(16) | curses.A_BOLD)
        for i in range(1, height - 1):
            stdscr.addstr(i, 0, "│".ljust(width - 1) + "│")
        stdscr.addstr(0, 0, "┌" + "─" * (width - 2) + "┐")
        stdscr.addstr(height - 1, 0, "└" + "─" * (width - 2) + "┘")
        stdscr.attroff(curses.color_pair(16) | curses.A_BOLD)
    except:
        pass

def main(stdscr):
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    
    try:
        colors = [
            (curses.COLOR_BLACK, -1), (curses.COLOR_RED, -1), (curses.COLOR_GREEN, -1),
            (curses.COLOR_YELLOW, -1), (curses.COLOR_BLUE, -1), (curses.COLOR_MAGENTA, -1),
            (curses.COLOR_CYAN, -1), (curses.COLOR_WHITE, -1)
        ]
        
        for i, (fg, bg) in enumerate(colors * 3):
            curses.init_pair(i + 1, fg + 8, bg)
        
        curses.init_pair(16, curses.COLOR_WHITE, -1)
        curses.init_pair(17, curses.COLOR_CYAN + 8, -1)
        curses.init_pair(18, curses.COLOR_MAGENTA + 8, -1)
        curses.init_pair(19, curses.COLOR_BLACK, curses.COLOR_YELLOW + 8)
        curses.init_pair(20, curses.COLOR_WHITE + 8, -1)
        curses.init_pair(21, curses.COLOR_GREEN + 8, -1)
        
        all_apps = get_installed_apps()
        filtered_apps = all_apps[:]
        selected = 0
        search_query = ''
        scroll_offset = 0
        edit_pos = 0
        search_focus = False
        app_count = len(all_apps)
        
        while True:
            height, width = stdscr.getmaxyx()
            stdscr.clear()
            
            draw_border(stdscr, height, width)
            
            try:
                stdscr.attron(curses.color_pair(17) | curses.A_BOLD)
                title = " gaveta de apps "
                title_pos = max(0, (width - len(title)) // 2)
                stdscr.addstr(0, title_pos, title)
                stdscr.attroff(curses.color_pair(17) | curses.A_BOLD)
                
                stdscr.attron(curses.color_pair(18) | curses.A_BOLD)
                search_text = f" 🔍 Search [{len(filtered_apps)}/{app_count}]: {search_query}"
                stdscr.addstr(1, 1, search_text[:width-2])
                if search_focus:
                    cursor_pos = 1 + len(f" 🔍 pesquisar [{len(filtered_apps)}/{app_count}]: {search_query[:edit_pos]}")
                    if cursor_pos < width - 1:
                        stdscr.addch(1, cursor_pos, ord('█'), curses.A_REVERSE | curses.A_BOLD)
                stdscr.attroff(curses.color_pair(18) | curses.A_BOLD)
                
                display_height = max(1, height - 5)
                start_y = 2
                
                for i in range(scroll_offset, min(scroll_offset + display_height, len(filtered_apps))):
                    y = start_y + (i - scroll_offset)
                    if y >= height - 2:
                        break
                    app_name = filtered_apps[i][0][:width - 8]
                    if i == selected:
                        stdscr.attron(curses.color_pair(19) | curses.A_BOLD)
                        stdscr.addstr(y, 2, f" ► {app_name}")
                        stdscr.attroff(curses.color_pair(19) | curses.A_BOLD)
                    else:
                        color = (i % 7) + 1
                        stdscr.attron(curses.color_pair(color))
                        stdscr.addstr(y, 2, f"   {app_name}")
                        stdscr.attroff(curses.color_pair(color))
                
                if not filtered_apps:
                    stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
                    no_apps_text = " 😔 Não temm nenhum app aqui "
                    stdscr.addstr(start_y + 1, max(0, (width - len(no_apps_text)) // 2), no_apps_text)
                    stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)
                
                scroll_info = f" {selected + 1}/{len(filtered_apps)} "
                stdscr.attron(curses.color_pair(21))
                info_pos = width - len(scroll_info) - 2
                if info_pos > 0:
                    stdscr.addstr(height - 2, info_pos, scroll_info)
                stdscr.attroff(curses.color_pair(21))
                
                focus_indicator = "[SEARCH]" if search_focus else "[BROWSE]"
                stdscr.attron(curses.color_pair(20) | curses.A_BOLD)
                help_text = f" {focus_indicator} | ↑↓: Navigate | Enter: Launch | Ctrl+F: Search | Ctrl+X: Clear | Ctrl+Q: Quit "
                help_pos = max(0, (width - len(help_text)) // 2)
                stdscr.addstr(height - 1, help_pos, help_text[:width - help_pos])
                stdscr.attroff(curses.color_pair(20) | curses.A_BOLD)
                
                stdscr.refresh()
            except:
                pass
            
            key = stdscr.getch()
            print(f"Key pressed: {key}")  # Debug - remove depois
            
            if key == 17:
                break
            elif key == 6:
                search_focus = True
                edit_pos = len(search_query)
            elif key == curses.KEY_UP:
                search_focus = False
                if selected > 0:
                    selected -= 1
                    if selected < scroll_offset:
                        scroll_offset -= 1
            elif key == curses.KEY_DOWN:
                search_focus = False
                if selected < len(filtered_apps) - 1:
                    selected += 1
                    if selected >= scroll_offset + display_height:
                        scroll_offset += 1
            elif key == curses.KEY_PPAGE:
                search_focus = False
                scroll_offset = max(0, scroll_offset - display_height)
                selected = min(selected, scroll_offset + display_height - 1)
            elif key == curses.KEY_NPAGE:
                search_focus = False
                scroll_offset = min(len(filtered_apps) - display_height, scroll_offset + display_height)
                selected = min(selected, scroll_offset + display_height - 1)
            elif key == 10 or key == 13:
                search_focus = False
                if filtered_apps:
                    curses.endwin()
                    launch_app(filtered_apps[selected][1])
                    stdscr = curses.initscr()
                    curses.noecho()
                    curses.cbreak()
                    stdscr.keypad(True)
                    curses.curs_set(0)
                    curses.start_color()
                    curses.use_default_colors()
            elif search_focus:
                handled = False
                if key == 127 or key == 8:
                    if edit_pos > 0:
                        search_query = search_query[:edit_pos-1] + search_query[edit_pos:]
                        edit_pos -= 1
                        handled = True
                elif key == curses.KEY_DC:
                    if edit_pos < len(search_query):
                        search_query = search_query[:edit_pos] + search_query[edit_pos+1:]
                        handled = True
                elif key == curses.KEY_LEFT:
                    edit_pos = max(0, edit_pos - 1)
                    handled = True
                elif key == curses.KEY_RIGHT:
                    edit_pos = min(len(search_query), edit_pos + 1)
                    handled = True
                elif key == 24:
                    search_query = ''
                    edit_pos = 0
                    handled = True
                elif 32 <= key <= 126:
                    search_query = search_query[:edit_pos] + chr(key) + search_query[edit_pos:]
                    edit_pos += 1
                    handled = True
                
                if handled:
                    filtered_apps = [app for app in all_apps if search_query.lower() in app[0].lower()] if search_query else all_apps[:]
                    selected = 0
                    scroll_offset = 0
            else:
                search_focus = False
            
            if not search_focus:
                filtered_apps = [app for app in all_apps if search_query.lower() in app[0].lower()] if search_query else all_apps[:]
                selected = min(selected, len(filtered_apps) - 1) if filtered_apps else 0
                scroll_offset = max(0, min(scroll_offset, max(0, len(filtered_apps) - display_height)))
            
    except KeyboardInterrupt:
        pass
    except:
        pass
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

if __name__ == "__main__":
    main(curses.initscr())
