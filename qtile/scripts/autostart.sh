#!/bin/bash

function run {
  if ! pgrep $1 ;
  then
    $@&
  fi
}

#Set your native resolution IF it does not exist in xrandr
#More info in the script
#run $HOME/.config/qtile/scripts/set-screen-resolution-in-virtualbox.sh

#Find out your monitor name with xrandr or arandr (save and you get this line)
#xrandr --output VGA-1 --primary --mode 1360x768 --pos 0x0 --rotate normal
#xrandr --output DP2 --primary --mode 1920x1080 --rate 60.00 --output LVDS1 --off &
#xrandr --output LVDS1 --mode 1366x768 --output DP3 --mode 1920x1080 --right-of LVDS1
#xrandr --output HDMI2 --mode 1920x1080 --pos 1920x0 --rotate normal --output HDMI1 --primary --mode 1920x1080 --pos 0x0 --rotate normal --output VIRTUAL1 --off
#xrandr --output HDMI-0 --primary --mode 1920x1080 --pos 0x0 --rotate normal --output DVI-I-1 --off --output DVI-I-0 --mode 1920x1080 --pos 1920x0 --rotate normal --output DP-1 --off --output DP-0 --off
#xrandr --output HDMI1 --primary --mode 1920x1080 --pos 0x0 --rotate normal --output VIRTUAL1 --off --output DP1 --off --output VGA1 --mode 1920x1080 --pos 1920x0 --rotate normal
xrandr --output DP-0 --off --output DP-1 --off --output DP-2 --mode 1920x1080 --pos 1920x0 --rotate normal --output DP-3 --off --output DP-4 --off --output DP-5 --off --output DP-6 --primary --mode 1920x1080 --pos 0x0 --rotate normal --output DP-7 --off

#polybar launch
#(sleep 2; run $HOME/.config/polybar/launch.sh) &

#Marco Test
#(sleep 2; run $HOME/.screenlayout/mylayout2.sh) &

#change your keyboard if you need it
#setxkbmap -layout be

#Some ways to set your wallpaper besides variety or nitrogen
feh --bg-fill /usr/share/backgrounds/arcolinux/arco-wallpaper.jpg &
#start the conky to learn the shortcuts
#(conky -c $HOME/.config/qtile/scripts/system-overview) &

#starting utility applications at boot time
run variety &
run nm-applet &
run pamac-tray &
run xfce4-power-manager &
numlockx on &
blueberry-tray &
picom --config $HOME/.config/qtile/scripts/picom.conf &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
/usr/lib/xfce4/notifyd/xfce4-notifyd &

#starting user applications at boot time
run volumeicon &
(sleep 3; run ~/.bin/ckb.sh) &
#run caffeine &
run discord &
#nitrogen --restore &
run caffeine -a &
#run firefox &
termite &
run thunar &
#run dropbox &
run VirtualBox &
run insync start &
#run spotify &
#run telegram-desktop &
run subl3 &
run vivaldi-stable &

#Marco Test
#(sleep 2; run $HOME/.screenlayout/mylayout2.sh) &

(sleep 15; VBoxManage startvm Win10x64) &
(sleep 25; VBoxManage startvm testvm1) &

