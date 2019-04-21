
keys = [

    #########################
    # SUPER + ... KEYS      #
    #########################
    Key([mod], "e", lazy.spawn('atom')),
    Key([mod], "f", lazy.window.toggle_fullscreen()),
    Key([mod], "h", lazy.spawn('urxvt -e htop')),
    #Key([mod], "m", lazy.spawn('pragha')),
    #Key([mod], "n", lazy.layout.normalize()),
    Key([mod], "q", lazy.spawn('firefox')),
    Key([mod], "r", lazy.spawncmd()),
    Key([mod], "s", lazy.spawn('rofi-theme-selector')),
    Key([mod], "t", lazy.spawn('termite')),
    Key([mod], "v", lazy.spawn('pavucontrol')),
    Key([mod], "w", lazy.spawn('vivaldi-stable')),
    Key([mod], "x", lazy.spawn('oblogout')),

    # Switch between windows in current stack pane
    #Key([mod], "k", lazy.layout.down()),
    #Key([mod], "j", lazy.layout.up()),
    #Key([mod], "l", lazy.layout.right()),
    #Key([mod], "h", lazy.layout.left()),

    # Move windows up or down in current stack
    Key([mod, "shift"], "k", lazy.layout.shuffle_up()),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down()),

    Key([mod, "shift"], "l", lazy.layout.shuffle_right()),
    Key([mod, "shift"], "h", lazy.layout.shuffle_left()),

    # Switch window focus to other pane(s) of stack
    Key(["mod1"], "Tab", lazy.layout.next()),
    Key(["mod1"], "space", lazy.layout.previous()),

    #Key([mod], "f", lazy.window.toggle_fullscreen()),
    Key([mod, "shift"], "f", lazy.window.toggle_floating()),

    Key([mod, "shift"], "Left", window_to_prev_group()),
    Key([mod, "shift"], "Right", window_to_next_group()),

    Key([mod], "Left", go_to_prev_group()),
    Key([mod], "Right", go_to_next_group()),

    Key([mod, "control"], "l",
        lazy.layout.grow_right(),
        lazy.layout.grow(),
        lazy.layout.increase_ratio(),
        lazy.layout.delete(),
        ),
    Key([mod, "control"], "h",
        lazy.layout.grow_left(),
        lazy.layout.shrink(),
        lazy.layout.decrease_ratio(),
        lazy.layout.add(),
        ),

    Key([mod, "control"], "k",
        lazy.layout.grow_up(),
        lazy.layout.grow(),
        lazy.layout.decrease_nmaster(),
        ),

    Key([mod, "control"], "j",
        lazy.layout.grow_down(),
        lazy.layout.shrink(),
        lazy.layout.increase_nmaster(),
        ),

    Key([mod], "m",
        lazy.layout.maximize(),
        ),

    Key([mod], "n",
        lazy.layout.normalize(),
        ),

    Key([mod, "mod1"], "k", lazy.layout.flip_up()),
    Key([mod, "mod1"], "j", lazy.layout.flip_down()),

    Key([mod, "mod1"], "l", lazy.layout.flip_right()),
    Key([mod, "mod1"], "h", lazy.layout.flip_left()),

    # Swap panes of split stack
    Key([mod, "shift"], "space",
        lazy.layout.rotate()
        ),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key([mod, "shift"], "Return", lazy.layout.toggle_split()),
    Key([mod], "Return", lazy.spawn()),

    # Toggle between different layouts as defined below
    Key([mod], "Tab", lazy.next_layout()),
    Key([mod], "space", lazy.prev_layout()),
    #Key([mod], "x", lazy.window.kill()),

    Key([mod, "shift"], "r", lazy.restart()),
    #Key([mod, "shift"], "q", lazy.shutdown()),
    Key([mod, "shift"], "Pause", exit_menu()),
    Key([mod, "shift"], "Scroll_Lock", lazy.spawn("/usr/bin/slock")),
    Key([mod, "shift", "control"], "Print", lazy.spawn("/usr/bin/systemctl -i suspend")),
    #Key([mod], "r", lazy.spawncmd()),
    Key([mod], "g", lazy.switchgroup()),



    # Applications
    Key([mod], "d", lazy.spawn("/usr/bin/rofi -modi run,drun -show drun run")),
    Key([mod], "Delete", lazy.function(find_or_run("/usr/bin/lxtask", ("Lxtask",),
                                                   cls_grp_dict["Lxtask"]))),
    Key([mod], "F1", lazy.function(find_or_run("/usr/bin/catfish", ("Catfish",),
                                              cls_grp_dict["Catfish"], ("^/usr/bin/python /usr/bin/catfish$",)))),
    #Key([mod], "e", lazy.function(find_or_run("/usr/bin/leafpad",
    #                                          ("Leafpad", "Mousepad", "Pluma"), cls_grp_dict["Leafpad"],
    #                                          (regex("leafpad"),
    #                                           regex("mousepad"), regex("pluma"))))),
    Key([mod, "shift"], "e", lazy.function(find_or_run("/usr/bin/geany", ("Geany", "kate"),
                                                       cls_grp_dict["Geany"], (regex("geany"), regex("kate"))))),
    Key([mod], "Home", lazy.function(find_or_run("/usr/bin/pcmanfm", ("Pcmanfm", "Thunar", "dolphin"),
                                                 cls_grp_dict["Pcmanfm"],
                                                 (regex("pcmanfm"), regex("thunar"), regex("dolphin"))))),
    Key([mod, "shift"], "Home", lazy.function(find_or_run(term + " -e /usr/bin/ranger", (),
                                                          cls_grp_dict["termite"]))),
    Key([mod], "p", lazy.function(find_or_run("/usr/bin/pragha", ("Pragha", "Clementine"),
                                              cls_grp_dict["Pragha"], [regex("pragha"), regex("clementine")]))),
    Key([mod], "c", lazy.function(find_or_run(term + " -e /usr/bin/cmus", (),
                                              cls_grp_dict["termite"]))),
    #Key([mod], "w", lazy.function(find_or_run("/usr/bin/firefox", ("Firefox", "Chromium", "Vivaldi-stable"),
    #                                          cls_grp_dict["Firefox"],
    #                                          ("/usr/lib/firefox/firefox", "/usr/lib/chromium/chromium",
    #                                           "/opt/vivaldi/vivaldi-bin")))),
    Key([mod, "shift"], "w", lazy.function(find_or_run(home +
                                                       "/Apps/Internet/tor-browser_en-US/Browser/start-tor-browser "
                                                       "--detach ", ("Tor Browser",), cls_grp_dict["Tor Browser"],
                                                       ("\./firefox",)))),
    Key([mod], "i", lazy.function(find_or_run("/usr/bin/pamac-manager", ["Pamac-manager"],
                                              cls_grp_dict["Pamac-manager"]))),
    Key([], "F10", to_urgent()),

    # Media player controls
    Key([], "XF86AudioPlay", lazy.spawn("/usr/bin/playerctl play")),
    Key([], "XF86AudioPause", lazy.spawn("/usr/bin/playerctl pause")),
    Key([], "XF86AudioNext", lazy.spawn("/usr/bin/playerctl next")),
    Key([], "XF86AudioPrev", lazy.spawn("/usr/bin/playerctl previous")),

    # Screenshot
    Key([], "Print", lazy.spawn("/usr/bin/scrot " + home + "/Pictures/Screenshots/screenshot_%Y_%m_%d_%H_%M_%S.png")),

    # Pulse Audio controls
    Key([], "XF86AudioMute",
        lazy.spawn("/usr/bin/pactl set-sink-mute alsa_output.pci-0000_00_1b.0.analog-stereo toggle")),
    Key([], "XF86AudioLowerVolume",
        lazy.spawn("/usr/bin/pactl set-sink-volume alsa_output.pci-0000_00_1b.0.analog-stereo -5%")),
    Key([], "XF86AudioRaiseVolume",
        lazy.spawn("/usr/bin/pactl set-sink-volume alsa_output.pci-0000_00_1b.0.analog-stereo +5%"))
]
