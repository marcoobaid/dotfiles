#!/bin/bash

function run {
  if ! pgrep $1 ;
  then
    $@&
  fi
}
#run "xrandr --output VGA-1 --primary --mode 1360x768 --pos 0x0 --rotate normal"
#run "xrandr --output HDMI2 --mode 1920x1080 --pos 1920x0 --rotate normal --output HDMI1 --primary --mode 1920x1080 --pos 0x0 --rotate normal --output VIRTUAL1 --off"
run xrandr --output DVI-I-1 --primary --mode 1920x1080 --pos 1920x0 --rotate normal --output DP-1 --off --output HDMI-1 --mode 1920x1080 --pos 0x0 --rotate normal

#$HOME/.config/polybar/launch.sh &
#setxkbmap -layout be
#feh --bg-scale ~/.config/qtile/wall.png &
#nitrogen --random --set-scaled
xsetroot -cursor_name left_ptr &
run nm-applet &
run variety &
run pamac-tray &
run xfce4-power-manager &
numlockx on &
#conky -c $HOME/.config/qtile/system-overview &
compton --config $HOME/.config/qtile/compton.conf &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
/usr/lib/xfce4/notifyd/xfce4-notifyd &
run volumeicon
#nitrogen --random --set-scaled
#nitrogen --restore &
#caffeine &
#dropbox &
#blueberry-tray &
#thunar &
#insync start &
