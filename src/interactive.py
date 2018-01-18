import curses


_mappings = [
    ["KEY_POWEROFF",      {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"ButtonEvent","Press":[303],"DeviceModel":"iPhone"}},         "Power off"],
    ["KEY_UP",            "Up",        "Up"],
    ["KEY_DOWN",          "Down",      "Down"],
    ["KEY_LEFT",          "Left",      "Left"],
]


def run(remote):
    """Run interactive remote control application."""
    curses.wrapper(_control, remote)


def _control(stdscr, remote):
    height, width = stdscr.getmaxyx()

    stdscr.addstr("Interactive mode, press 'Q' to exit.\n")
    stdscr.addstr("Key mappings:\n")

    column_len = max(len(mapping[2]) for mapping in _mappings) + 1
    mappings_dict = {}
    for mapping in _mappings:
        mappings_dict[mapping[0]] = mapping[1]

        row = stdscr.getyx()[0] + 2
        if row < height:
            line = "  {}= {} ({})\n".format(mapping[2].ljust(column_len),
                                            mapping[3], mapping[1])
            stdscr.addstr(line)
        elif row == height:
            stdscr.addstr("[Terminal is too small to show all keys]\n")

    running = True
    while running:
        key = stdscr.getkey()

        if key == "q":
            running = False

        if key in mappings_dict:
            remote.control(mappings_dict[key])

            try:
                stdscr.addstr(".")
            except curses.error:
                stdscr.deleteln()
                stdscr.move(stdscr.getyx()[0], 0)
                stdscr.addstr(".")
