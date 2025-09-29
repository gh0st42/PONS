#!/bin/bash

set -e

# in case of errors kill the tmux session
# create new tmux session
SESSION_NAME="dtnmail"
trap "tmux kill-session -t $SESSION_NAME" ERR

tmux new-session -d -s $SESSION_NAME


# rename the first window to "DTN Mail Servers"
tmux rename-window -t $SESSION_NAME:0 "n1"
# start bpimapd in servers window
tmux send-keys -t $SESSION_NAME:0 "python3 bpimapd.py --host localhost --port 1143 --udp-in 10102 -d n1.space" C-m
# split the window vertically
tmux split-window -t $SESSION_NAME:0
# start bpsmtpd in servers window
tmux send-keys -t $SESSION_NAME:0 "python3 bpsmtpd.py --port 1025 --udp-out localhost:10101 --dtn-dst ipn:3.25 -d n1.space" C-m

tmux new-window -t $SESSION_NAME:1 -n "n3"
# start bpimapd in servers window
tmux send-keys -t $SESSION_NAME:1 "python3 bpimapd.py --host localhost --port 2143 --udp-in 10202 -d n2.space" C-m
# split the window vertically
tmux split-window -t $SESSION_NAME:1
# start bpsmtpd in servers window
tmux send-keys -t $SESSION_NAME:1 "python3 bpsmtpd.py --port 2025 --udp-out localhost:10201 --dtn-dst ipn:1.25 -d n2.space" C-m

# create new window for the simulation
tmux new-window -t $SESSION_NAME:2 -n "Main Sim"
tmux send-keys -t $SESSION_NAME:2 "LOG_FILE=/tmp/dtnmail.log python3 dtnmail.py" C-m

# create new window for the tests
tmux new-window -t $SESSION_NAME:3 -n "Tests"

tmux send-keys -t $SESSION_NAME:3 "python3 test_send.py -H localhost -p 1025 -s 'test 1' -f alex@n1.space -t jamie@n2.space"
# split the tests window vertically
tmux split-window -t $SESSION_NAME:3
# run the test_receive.py in the new pane
tmux send-keys -t $SESSION_NAME:3 "python3 test_recv.py -H localhost -p 2143 "

# create window for terminating this session
tmux new-window -t $SESSION_NAME:4 -n "Shutdown"
tmux send-keys -t $SESSION_NAME:4 "clear && echo 'Press any key to terminate the session...' && read -n 1 -s && tmux kill-session -t $SESSION_NAME" C-m

# select the second window (Main Simulation)
tmux select-window -t $SESSION_NAME:2

# set mouse mode
tmux set -g mouse on

# attach to the session
tmux attach -t $SESSION_NAME