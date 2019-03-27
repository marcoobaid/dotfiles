import pickle
import weakref
from contextlib import contextmanager, suppress
from datetime import datetime
from itertools import islice
from logging import getLogger
from pathlib import Path

from libqtile import bar, hook, layout, widget
from libqtile.command import lazy
from libqtile.config import Click, Drag, Group, Key, Screen, Rule, Match
from libqtile.widget.base import ORIENTATION_HORIZONTAL
from libqtile.widget.base import _TextBox as BaseTextBox

logger = getLogger('qtile.config')


# TODO: multiple micro indicators will poll pulseaudio independently
# TODO: microphone icon rendered
# TODO: volume indicator
# TODO: separate indicators for several microphones and outputs
# TODO: background images for each group
# TODO: backgrounds and proper drawing for bar
# TODO: keyboard indicator/switcher
# TODO: caps lock & group switching bug
# TODO: screenshots without stealing focus
# TODO: click on notification should reveat freshly made screenshot
# TODO: automatically add additional groups ??
# TODO: automatically clean clipboard after some time
# TODO: schematic window layouts under group letters

import os
import subprocess

@hook.subscribe.startup_once
def autostart():
    home = os.path.expanduser('~/.config/qtile/autostart.sh')
    subprocess.call([home])

class PulseContext:
    VOLUME_STEP = 0.05

    def __init__(self, pulse, ctl):
        self._pulse = weakref.ref(pulse)
        self._ctl = ctl

    @property
    def pulse(self):
        return self._pulse()

    def _change_volume(self, inc):
        for obj in self.pulse.sink_list():
            obj.volume.values = [min(1, max(0, v + inc)) for v in obj.volume.values]
            self.pulse.volume_set(obj, obj.volume)

    def mute(self):
        for obj in self.pulse.sink_list():
            self.pulse.mute(obj, mute=not obj.mute)

    def raise_volume(self):
        self._change_volume(self.VOLUME_STEP)

    def lower_volume(self):
        self._change_volume(-self.VOLUME_STEP)

    def get_micro(self):
        mute = True
        for obj in self.pulse.source_list():
            mute &= obj.mute
        return mute

    def toggle_micro(self):
        mute = not self.get_micro()
        for obj in self.pulse.source_list():
            self.pulse.mute(obj, mute=mute)
        for cb in self._ctl._micro_callbacks:
            cb(mute)
        return mute


class PulseControl:
    def __init__(self):
        self.Pulse = None
        try:
            from pulsectl import Pulse
        except ImportError:
            logger.error('You have to pip install pulsectl')
        else:
            self.Pulse = Pulse
        self._micro_callbacks = []

    @property
    def valid(self):
        return self.Pulse is not None

    @contextmanager
    def context(self):
        with self.Pulse('qtile-config') as pulse:
            yield PulseContext(pulse, self)

    def make_cmd(self, func):
        def wrap(qtile):
            if self.valid:
                with self.context() as pctx:
                    func(pctx)
        return lazy.function(wrap)

    def register_micro_indicator(self, callback):
        self._micro_callbacks.append(callback)
        with self.context() as pctx:
            callback(pctx.get_micro())


class Timer:
    def __init__(self):
        self.reset()

    @property
    def current_gap(self):
        if self._current is None:
            return 0
        return (datetime.now() - self._current).total_seconds()

    @property
    def active(self):
        return self._current is not None

    @active.setter
    def active(self, value):
        if value == self.active:
            return
        if value:
            self._current = datetime.now()
        else:
            self._summed += self.current_gap
            self._current = None

    def reset(self):
        self._summed = 0
        self._current = None

    @property
    def seconds(self):
        return self._summed + self.current_gap

    def __getstate__(self):
        # dict prevents value to be false
        return {'seconds': self.seconds}

    def __setstate__(self, d):
        self._summed = d['seconds']
        self._current = None


class MulticlickDetector:
    def __init__(self, clicks=3, time_period=2.0):
        assert clicks > 1
        assert time_period > 0

        self.clicks = clicks
        self.time_period = time_period

        self.counter = 0
        self.last = datetime.now()

    def click(self):
        now = datetime.now()
        if (now - self.last).total_seconds() > self.time_period:
            self.counter = 0
            self.last = now

        self.counter += 1
        if self.counter < self.clicks:
            return False
        self.counter = 0
        return True


class PersistenceFilter:
    def __init__(self, timer: Timer):
        self.olddata = pickle.dumps(timer)

    def update(self, timer: Timer):
        newdata = pickle.dumps(timer)
        if newdata == self.olddata:
            return False, None
        self.olddata = newdata
        return True, newdata


class TimerPersistence:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self):
        timer = None
        with suppress(FileNotFoundError, EOFError, pickle.UnpicklingError):
            # TODO: check writable
            timer = pickle.loads(self.file_path.read_bytes())
        if timer is None:
            timer = Timer()
        self.pfilter = PersistenceFilter(timer)
        return timer

    def flush(self, timer):
        should, bindata = self.pfilter.update(timer)
        if not should:
            return
        # TODO: check writable
        self.file_path.write_bytes(bindata)


def format_timer(timer: Timer, spinner=True) -> str:
    spinner_chars = '⣾⣽⣻⢿⡿⣟⣯⣷'

    def ft(s: int) -> str:
        too_small = s < 5 * 60
        result = []
        if s >= 3600:
            result.append(str(s // 3600) + 'h')
            s %= 3600
        if s >= 60:
            result.append(str(s // 60) + 'm')
            s %= 60
        if too_small:
            result.append(str(s) + 's')
        return ' '.join(result)

    if not timer.active and timer.seconds <= 0:
        return '⌚'
    s = int(timer.seconds)
    result = ft(s)
    if spinner:
        result += spinner_chars[s % len(spinner_chars)]
    return result


class CustomBaseTextBox(BaseTextBox):
    defaults = [
        ("text_shift", 0, "Shift text vertically"),
    ]

    def __init__(self, text=" ", width=bar.CALCULATED, **config):
        super().__init__(text, width, **config)
        self.add_defaults(CustomBaseTextBox.defaults)

    # exact copy of original code, with Y adjustment
    def draw(self):
        # if the bar hasn't placed us yet
        if self.offsetx is None:
            return
        self.drawer.clear(self.background or self.bar.background)
        self.layout.draw(
            self.actual_padding or 0,
            int(self.bar.height / 2.0 - self.layout.height / 2.0) + 1 + self.text_shift,  # here
        )
        self.drawer.draw(offsetx=self.offsetx, width=self.width)


class CustomCurrentLayout(CustomBaseTextBox):
    orientations = ORIENTATION_HORIZONTAL

    def __init__(self, width=bar.CALCULATED, **config):
        super().__init__(text='', width=width, **config)

    @staticmethod
    def get_layout_name(name):
        return ({
            'max': '▣',
            'columns': '▥',
            'bsp': '◫',
        }).get(name, '[{}]'.format(name))

    def _configure(self, qtile, bar):
        BaseTextBox._configure(self, qtile, bar)
        self.text = self.get_layout_name(self.bar.screen.group.layouts[0].name)
        self.setup_hooks()

    def setup_hooks(self):
        def hook_response(layout, group):
            if group.screen is not None and group.screen == self.bar.screen:
                self.text = self.get_layout_name(layout.name)
                self.bar.draw()
        hook.subscribe.layout_change(hook_response)

    def button_press(self, x, y, button):
        if button == 1:
            self.qtile.cmd_next_layout()
        elif button == 2:
            self.qtile.cmd_prev_layout()


class MicroIndicator(CustomBaseTextBox):
    orientations = ORIENTATION_HORIZONTAL
    defaults = [
        ('active_color', 'ff0000', 'Color of active indicator'),
        ('inactive_color', '888888', 'Color of inactive indicator'),
    ]

    def get_color(self, mute):
        return self.inactive_color if mute else self.active_color

    def __init__(self, *, pulse_ctl, width=bar.CALCULATED, **config):
        super().__init__(text='⚫', width=width, **config)
        self.add_defaults(MicroIndicator.defaults)
        self.pulse_ctl = pulse_ctl
        self.pulse_ctl.register_micro_indicator(self.update_indicator)

    def update_indicator(self, mute):
        new_color = self.get_color(mute)
        if self.foreground == new_color:
            return
        self.foreground = new_color
        if self.configured:
            # TODO: don't redraw whole bar
            self.bar.draw()

    def cmd_toggle(self):
        "Toggle microphone."
        with self.pulse_ctl.context() as pctx:
            pctx.toggle_micro()

    def button_press(self, x, y, button):
        if button == 1:
            self.cmd_toggle()

    def timer_setup(self):
        self.timeout_add(3, self._auto_update)

    def _auto_update(self):
        with self.pulse_ctl.context() as pctx:
            mute = pctx.get_micro()
        self.update_indicator(mute)
        self.timeout_add(2, self._auto_update)


class TimeTracker(CustomBaseTextBox):
    orientations = ORIENTATION_HORIZONTAL
    defaults = [
        ('active_color', 'ff4000', 'Color of active indicator'),
        ('inactive_color', '888888', 'Color of inactive indicator'),
        ('update_interval', 1, 'Update interval in seconds'),
        ('save_interval', 300, 'Interval in seconds for persistence'),
    ]

    def __init__(self, **config):
        super().__init__(text='', **config)
        self.add_defaults(TimeTracker.defaults)
        self.persist = TimerPersistence(Path.home() / '.tracker')
        self.timer = self.persist.load()
        self.resblocker = MulticlickDetector()
        self.formatter = format_timer
        self.update()
        if self.padding is None:
            self.padding = 4

    def cmd_toggle(self):
        "Toggles timer (pause/unpause)."
        self.timer.active = not self.timer.active
        self.update()

    def cmd_reset(self):
        "Resets timer."
        self.timer.reset()
        self.update()

    def cmd_read(self, humanize=True):
        "Current amount of seconds."
        if humanize:
            return self.formatter(self.timer, spinner=False)
        return self.timer.seconds

    def button_press(self, x, y, button):
        if button == 1:
            self.cmd_toggle()
        elif button == 3:
            if self.resblocker.click():
                self.cmd_reset()

    def update(self):
        new_text = self.formatter(self.timer)
        new_color = self.active_color if self.timer.active else self.inactive_color

        redraw = False
        redraw_bar = False

        old_width = None
        if self.layout:
            old_width = self.layout.width

        if new_color != self.foreground:
            redraw = True
            self.foreground = new_color

        if new_text != self.text:
            redraw = True
            self.text = new_text

        if not self.configured:
            return

        if self.layout.width != old_width:
            redraw_bar = True

        if redraw_bar:
            self.bar.draw()
        elif redraw:
            self.draw()

    def timer_setup(self):
        self.timeout_add(self.update_interval, self._auto_update)
        self.timeout_add(self.save_interval, self._auto_persist)

    def _auto_update(self):
        self.update()
        self.timeout_add(self.update_interval, self._auto_update)

    def _auto_persist(self):
        self.persist.flush(self.timer)
        self.timeout_add(self.save_interval, self._auto_persist)


hook.subscribe.hooks.add('prompt_focus')
hook.subscribe.hooks.add('prompt_unfocus')


class CustomPrompt(widget.Prompt):
    def startInput(self, *a, **kw):  # noqa: N802
        hook.fire('prompt_focus')
        return super().startInput(*a, **kw)

    def _unfocus(self):
        hook.fire('prompt_unfocus')
        return super()._unfocus()


class CustomWindowName(widget.WindowName):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.visible = True

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        hook.subscribe._subscribe('prompt_focus', self.hide)
        hook.subscribe._subscribe('prompt_unfocus', self.show)

    def show(self):
        self.visible = True
        self.update()

    def hide(self):
        self.visible = False
        self.update()

    def update(self, *args):
        if self.visible:
            super().update(*args)
        else:
            self.text = ''
            self.bar.draw()


pulse_ctl = PulseControl()

#groups = []
#for gname in 'asdfghjkl':
#    groups.append(Group(gname, label=gname.upper()))

#groups = []
#for gname in '123456789':
#    groups.append(Group(gname, label=gname.upper()))

#groups = [
#    Group("1", lablel=),
#    Group("2", lablel=),
#    Group("3", lablel=),
#    Group("4", lablel=),
#    Group("5", lablel=),
#    Group("6", lablel=),
#    Group("7", lablel=),
#    Group("8", lablel=),
#    Group("9", lablel=),
#]

groups = [
    Group("1"),
    Group("2"),
    Group("3"),
    Group("4"),
    Group("5"),
    Group("6"),
    Group("7"),
    Group("8"),
    Group("9"),
]

### Fix conflict with mod + h and others (refer to notes)
def user_keymap(mod, shift, control, alt):
    for g in groups:
        yield mod + g.name, lazy.group[g.name].toscreen()
        yield mod + shift + g.name, lazy.window.togroup(g.name)

    # MWO - My Keymaps

    #########################
    # SUPER + ... KEYS      #
    #########################
    yield mod + 'e', lazy.spawn('atom')
    yield mod + 'f', lazy.window.toggle_fullscreen()
    yield mod + 'h', lazy.spawn('urxvt -e htop')
    yield mod + 'm', lazy.spawn('pragha')
    yield mod + 'n', lazy.layout.normalize()
    yield mod + 'q', lazy.spawn('firefox')
    yield mod + 'r', lazy.spawnqcmd()
    yield mod + 's', lazy.spawn('rofi-theme-selector')
    yield mod + 't', lazy.spawn('termite')
    yield mod + 'v', lazy.spawn('pavucontrol')
    yield mod + 'w', lazy.spawn('vivaldi-stable')
    yield mod + 'x', lazy.spawn('oblogout')
    #########################
    # SUPER + FUNCTION KEYS #
    #########################
    yield mod + 'F1', lazy.spawn('vivaldi-stable')
    yield mod + 'F2', lazy.spawn('atom')
    yield mod + 'F3', lazy.spawn('inkscape')
    yield mod + 'F4', lazy.spawn('gimp')
    yield mod + 'F5', lazy.spawn('meld')
    yield mod + 'F6', lazy.spawn('vlc --video-on-top')
    yield mod + 'F7', lazy.spawn('virtualbox')
    yield mod + 'F8', lazy.spawn('thunar')
    yield mod + 'F9', lazy.spawn('evolution')
    yield mod + 'F10', lazy.window.toggle_floating()
    yield mod + 'F11', lazy.spawn('rofi -show run -fullscreen')
    yield mod + 'F12', lazy.spawn('rofi -show run')
    #########################
    # SUPER + SHIFT KEYS    #
    #########################
    yield mod + shift + 'Return', lazy.spawn('thunar')
    yield mod + shift + 'm', lazy.spawn("dmenu_run -i -nb '#191919' -nf '#fea63c' -sb '#fea63c' -sf '#191919' -fn 'NotoMonoRegular:bold:pixelsize=14'")
    yield mod + shift + 'q', lazy.window.kill()
    yield mod + shift + 'r', lazy.restart()
    yield mod + shift + 'x', lazy.shutdown()
    yield mod + shift + 'Down', lazy.layout.shuffle_down()
    yield mod + shift + 'Up', lazy.layout.shuffle_up()
    yield mod + shift + 'Left', lazy.layout.shuffle_left()
    yield mod + shift + 'Right', lazy.layout.shuffle_right()
    #########################
    # CONTROL + ALT KEYS    #
    #########################
    yield control + alt + 'a', lazy.spawn('atom')
    yield control + alt + 'b', lazy.spawn('thunar')
    yield control + alt + 'c', lazy.spawn('Catfish')
    yield control + alt + 'e', lazy.spawn('evolution')
    yield control + alt + 'f', lazy.spawn('firefox')
    yield control + alt + 'g', lazy.spawn('chromium -no-default-browser-check')
    yield control + alt + 'i', lazy.spawn('nitrogen')
    yield control + alt + 'k', lazy.spawn('slimlock')
    yield control + alt + 'm', lazy.spawn('xfce4-settings-manager')
    yield control + alt + 'o', lazy.spawn('~/.config/bspwm/scripts/compton-toggle.sh')
    yield control + alt + 'r', lazy.spawn('rofi-theme-selector')
    yield control + alt + 's', lazy.spawn('subl3')
    yield control + alt + 't', lazy.spawn('termite')
    yield control + alt + 'u', lazy.spawn('pavucontrol')
    yield control + alt + 'v', lazy.spawn('vivaldi-stable')
    yield control + alt + 'w', lazy.spawn('atom')
    yield control + alt + 'Return', lazy.spawn('termite')
    #########################
    # ALT + ... KEYS        #
    #########################
    yield alt + 't', lazy.spawn('variety -t')
    yield alt + 'n', lazy.spawn('variety -n')
    yield alt + 'p', lazy.spawn('variety -p')
    yield alt + 'f', lazy.spawn('variety -f')
    yield alt + 'Left', lazy.spawn('variety -p')
    yield alt + 'Right', lazy.spawn('variety -n')
    yield alt + 'Up', lazy.spawn('variety --pause')
    yield alt + 'Down', lazy.spawn('variety --resume')
    yield alt + 'F2', lazy.spawn('gmrun')
    yield alt + 'F3', lazy.spawn('xfce4-appfinder')
    #########################
    #VARIETY KEYS WITH PYWAL#
    #########################
    yield alt + shift + 't', lazy.spawn('variety -t && wal -i $(cat $HOME/.config/variety/wallpaper/wallpaper.jpg.txt)&')
    yield alt + shift + 'p', lazy.spawn('variety -p && wal -i $(cat $HOME/.config/variety/wallpaper/wallpaper.jpg.txt)&')
    yield alt + shift + 'f', lazy.spawn('variety -f && wal -i $(cat $HOME/.config/variety/wallpaper/wallpaper.jpg.txt)&')
    yield alt + shift + 'u', lazy.spawn('wal -i $(cat $HOME/.config/variety/wallpaper/wallpaper.jpg.txt)&')
    #yield alt + shift + 'u', lazy.spawn('wal -i $(cat /home/sysadmin/.config/variety/wallpaper/wallpaper.jpg.txt)&')
    #########################
    # CONTROL + SHIFT KEYS  #
    #########################
    yield control + shift + 'Escape', lazy.spawn('xfce4-taskmanager')
    #########################
    #     SCREENSHOTS       #
    #########################
    yield mod + 'Print', lazy.spawn('xfce4-screenshooter')
    yield mod + shift + 'Print', lazy.spawn('gnome-screenshot -i')
    yield 'Print', lazy.spawn("scrot 'ArcoLinuxD-%Y-%m-%d-%s_screenshot_$wx$h.jpg' -e 'mv $f $$(xdg-user-dir PICTURES)'")
    #########################
    #     MULTIMEDIA KEYS   #
    #########################


    yield mod + 'Return', lazy.spawn('termite')
    #yield mod + 'Escape', lazy.spawn('xkill')

    #########################
    # Qtile LAYOUT KEYS     #
    #########################
    yield mod + 'Down', lazy.layout.down()
    yield mod + 'Up', lazy.layout.up()
    yield mod + 'Left', lazy.layout.left()
    yield mod + 'Right', lazy.layout.right()

    yield mod + control + 'Down', lazy.layout.grow_down()
    yield mod + control + 'Up', lazy.layout.grow_up()
    yield mod + control + 'Left', lazy.layout.grow_left()
    yield mod + control + 'Right', lazy.layout.grow_right()

    yield mod + alt + 'Down', lazy.layout.flip_down()
    yield mod + alt + 'Up', lazy.layout.flip_up()
    yield mod + alt + 'Left', lazy.layout.flip_left()
    yield mod + alt + 'Right', lazy.layout.flip_right()



    yield mod + 'Tab', lazy.next_layout()

    yield mod + control + 'r', lazy.restart()
    yield mod + control + 'q', lazy.shutdown()

    #yield mod + 'F10', lazy.window.toggle_floating()
    #yield mod + 'F11', lazy.window.toggle_fullscreen()

    yield 'XF86AudioMute', pulse_ctl.make_cmd(lambda pctx: pctx.mute())
    yield 'XF86AudioRaiseVolume', pulse_ctl.make_cmd(lambda pctx: pctx.raise_volume())
    yield 'XF86AudioLowerVolume', pulse_ctl.make_cmd(lambda pctx: pctx.lower_volume())

    yield 'XF86HomePage', lazy.spawn('firefox')
    yield 'XF86Tools', lazy.spawn('audacious')
    yield 'XF86Mail', lazy.spawn('goldendict')
    yield 'XF86Explorer', lazy.spawn('nautilus')

    shutter = 'shutter --exit_after_capture --no_session --disable_systray '

    #yield mod + 'Print', lazy.spawn(shutter + '--active')
    #yield mod + control + 'Print', lazy.spawn(shutter + '--full')
##############################################################################

def make_keymap(user_map):
    result = []

    class KeyCombo:
        def __init__(self, mods, key):
            self._mods = mods
            self._key = key

    class KeyMods:
        def __init__(self, mods):
            self._mods = set(mods)

        def __add__(self, other):
            if isinstance(other, KeyMods):
                return KeyMods(self._mods | other._mods)
            else:
                return KeyCombo(self._mods, other)

    for k, cmd in user_map(
        KeyMods({'mod4'}),
        KeyMods({'shift'}),
        KeyMods({'control'}),
        KeyMods({'mod1'}),
    ):
        if isinstance(k, str):
            mods = set()
        elif isinstance(k, KeyCombo):
            mods = k._mods
            k = k._key
        else:
            logger.error('Bad key %s', k)
            continue

        if 'lock' in mods:
            logger.error('You must not use "lock" modifier yourself')
            continue

        result.append(Key(list(mods), k, cmd))

    return result


keys = make_keymap(user_keymap)


class DarkWallpaperColorBox:
    text = '000000'
    inactive_text = '9b8976'

    bg = 'e4ceb1'
    highlight_bg = 'd0aa78'
    urgent_bg = 'b81111'

    border = '7a6e5e'
    border_focus = urgent_bg
    highlight_text = urgent_bg


class GentooColorBox:
    bg = '54487A'
    highlight_bg = '6e56af'
    urgent_bg = '73d216'

    text = 'ffffff'
    inactive_text = '776a9c'

    border = '61538d'
    border_focus = urgent_bg
    highlight_text = urgent_bg


class LightWallpaperColorBox:
    bg = '666666'
    highlight_bg = '888888'
    urgent_bg = 'fe8964'

    text = 'ffffff'
    inactive_text = '333333'

    border = '333333'
    border_focus = urgent_bg
    highlight_text = urgent_bg


ColorBox = LightWallpaperColorBox


class ScreenProxy:
    def __init__(self, real_screen, margin):
        self._s = real_screen
        self._margin = margin

    @property
    def x(self):
        return self._s.x + self._margin

    @property
    def y(self):
        return self._s.y + self._margin

    @property
    def width(self):
        return self._s.width - self._margin * 2

    @property
    def height(self):
        return self._s.height - self._margin * 2


class FixedBsp(layout.Bsp):
    def configure(self, client, screen):
        amount = sum(1 for c in islice(self.root.clients(), 0, 2))
        super().configure(
            client,
            ScreenProxy(screen, self.margin if amount > 1 else -self.margin))


layouts = [
    FixedBsp(
        border_width=3,
        border_normal=ColorBox.border,
        border_focus=ColorBox.border_focus,
        margin=5,
        name='bsp',
    ),
    layout.Max(),
]
floating_layout = layout.Floating(
    border_width=3,
    border_normal=ColorBox.border,
    border_focus=ColorBox.border_focus,
    float_rules=[
        {'wmclass': 'confirm'},
        {'wmclass': 'dialog'},
        {'wmclass': 'download'},
        {'wmclass': 'error'},
        {'wmclass': 'file_progress'},
        {'wmclass': 'notification'},
        {'wmclass': 'splash'},
        {'wmclass': 'toolbar'},
        {'wmclass': 'confirmreset'},  # gitk
        {'wmclass': 'makebranch'},  # gitk
        {'wmclass': 'maketag'},  # gitk
        {'wname': 'branchdialog'},  # gitk
        {'wname': 'pinentry'},  # GPG key password entry
        {'wmclass': 'oblogout'},  # Oblogout Menu
        {'wmclass': 'xfce4-appfinder'},  # Application Finder
    ],
)


widget_defaults = dict(
    font='PT Sans',
    fontsize=16,
    padding=0,
    padding_x=0,
    padding_y=0,
    margin=0,
    margin_x=0,
    margin_y=0,
    foreground=ColorBox.text,
    center_aligned=True,
    markup=False,
)


def create_widgets():
    yield widget.GroupBox(
        disable_drag=True,
        use_mouse_wheel=False,
        padding_x=4,
        padding_y=0,
        margin_y=4,
        spacing=0,
        borderwidth=0,
        highlight_method='block',
        urgent_alert_method='block',
        rounded=False,
        active=ColorBox.text,
        inactive=ColorBox.inactive_text,
        urgent_border=ColorBox.urgent_bg,
        this_current_screen_border=ColorBox.highlight_bg,
        fontsize=32,
        font='Old-Town',
    )
    yield CustomPrompt(
        padding=10,
        foreground=ColorBox.highlight_text,
        cursor_color=ColorBox.highlight_text,
    )
    yield CustomWindowName(padding=10)
    yield widget.Systray()
    yield TimeTracker(
        active_color=ColorBox.highlight_text,
        inactive_color=ColorBox.inactive_text,
    )
    yield widget.Clock(
        format='%e %a',
        foreground=ColorBox.inactive_text,
        font='PT Serif',
        update_interval=60,
        padding=2,
    )
    yield widget.Clock(
        format='%H:%M',
        foreground=ColorBox.text,
        fontsize=18,
        font='Old-Town',
        padding=2,
    )
    if pulse_ctl.valid:
        yield MicroIndicator(
            pulse_ctl=pulse_ctl,
            active_color=ColorBox.highlight_text,
            inactive_color=ColorBox.inactive_text,
            fontsize=24,
            text_shift=-1,
        )
    yield CustomCurrentLayout(
        padding=0,
        fontsize=26,
        foreground=ColorBox.inactive_text,
        text_shift=-3,
    )


screens = [
    Screen(
        top=bar.Bar(
            list(create_widgets()),
            22,
            background=ColorBox.bg,
        ),
    ),
]


mouse = [
    Drag(['control'], 'Button9', lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag(['mod4'], 'Button9', lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([], 'Button9', lazy.widget['microindicator'].toggle(), focus=None),
]


dgroups_key_binder = None
dgroups_app_rules = []
main = None
follow_mouse_focus = False
bring_front_click = True
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = 'urgent'


# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, github issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = 'LG3D'
