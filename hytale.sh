#!/bin/bash
# ======================================================================
# Hytale Commander
# A command-line tool for managing a Hytale dedicated server.
#
# Usage: hytale.sh [command]
#
# Commands:
#   backup    - Create a timestamped backup of the world file
#   check     - Check current and latest Hytale version
#   console   - Attach to the Hytale server console
#   restart   - Restart the Hytale server
#   start     - Start the Hytale server
#   status    - Check if the server is running
#   stop      - Stop the Hytale server
#   tail      - Display last 15 lines of logs (errors highlighted)
#   update    - Download and install latest Hytale version
#
# Written 2025-01-17 on Fedora for Hytale
# ======================================================================

update_dir="$HOME/Sources"
working_dir="$HOME/Sources/hytale/Server"
backup_dir="/media/Synology/Michael/Backup/Hytale"
hytale_universe="$working_dir/universe"

hytale_port=25566
hytale_memory="-Xms6G -Xmx6G"
hytale_log="$working_dir/logs/latest.log"
hytale_downloader="$HOME/Sources/hytale/hytale-downloader-linux-amd64"
cd $working_dir || exit
mkdir -p $working_dir/mods/


# ------
# Colors
# Output text in color
red() { echo -e "\033[38;2;251;73;52m$*\033[0m"; }
blue() { echo -e "\033[38;2;166;173;232m$*\033[0m"; }
dark() { echo -e "\033[38;2;30;30;30m$*\033[0m"; }


# ------------
# Hytale Start
# Start the Hytale server in a detached screen session
# Wait for server to start (check log for success message)
HytaleStart() {
  if screen -list | grep -q "hytale"; then
    echo "  Hytale server is already running"
    return 1
  fi
  rm -f "$hytale_log"
  mkdir -p "$working_dir/logs"
  echo "  Starting Hytale server"
  screen -dmS hytale bash -c "java $hytale_memory -jar HytaleServer.jar --assets Assets.zip --bind 0.0.0.0:$hytale_port 2>&1 | tee $hytale_log"
  local elapsed=0 timeout=60
  while [ $elapsed -lt $timeout ]; do
    if [ -f "$hytale_log" ]; then
      if grep -q "Hytale.Server.Booted" "$hytale_log" 2>/dev/null; then
        echo "  Hytale server started successfully in screen session 'hytale'"
        return 0
      fi
      if grep -qi "ERROR\]" "$hytale_log" 2>/dev/null; then
        red "Hytale server failed to start"
        echo ""; HytaleTail
        return 1
      fi
    fi
    sleep 1
    ((elapsed++))
  done
  echo "  Timeout waiting for server startup confirmation"
  echo ""; HytaleTail
  return 1
}


# -----------
# Hytale Stop
# Stop the Hytale server.
# Wait for graceful shutdown, then force kill if necessary
HytaleStop() {
  if ! screen -list | grep -q "hytale"; then
    echo "  Hytale server is not running"
    return 1
  fi
  echo "  Stopping Hytale server"
  screen -S hytale -X stuff "/stop$(printf '\r')"
  local elapsed=0 timeout=15
  while [ $elapsed -lt $timeout ]; do
    if ! screen -list | grep -q "hytale"; then
      echo "  Hytale server stopped successfully"
      return 0
    fi
    sleep 1
    ((elapsed++))
  done
  echo "  Server didn't stop gracefully, forcing shutdown"
  screen -S hytale -X quit
  echo "  Hytale server stopped"
}


# --------------
# Hytale Restart
# Restart the Hytale server
HytaleRestart() {
  HytaleStop
  sleep 2
  HytaleStart
}


# -------------
# Hytale Status
# Check if the Hytale server is running
HytaleStatus() {
  if screen -list | grep -q "hytale"; then
    local world_name=$(basename "$hytale_universe")
    local world_size=$(du -sh "$hytale_universe" 2>/dev/null | cut -f1)
    local pid=$(pgrep -f "^java.*HytaleServer" | head -1)
    local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    local cpu_raw=$(ps -o %cpu= -p "$pid" 2>/dev/null | tr -d ' ')
    local cpu_cores=$(nproc)
    local cpu_usage=$(echo "$cpu_raw $cpu_cores" | awk '{printf "%.1f", $1/$2}')
    local mem_usage=$(ps -o rss= -p "$pid" 2>/dev/null | numfmt --to=iec --from-unit=1024)
    # Check for online players
    # Send /who command to server and capture response
    local log_size_before=$(wc -l < "$hytale_log" 2>/dev/null || echo 0)
    screen -S hytale -X stuff "/who$(printf '\r')"
    sleep 0.5
    local new_entries=$(tail -n +$((log_size_before + 1)) "$hytale_log" 2>/dev/null)
    local player_count=$(echo "$new_entries" | grep -oP 'default \(\K\d+(?=\):)' | head -1)
    [ -z "$player_count" ] && player_count="0"
    # Print the status
    echo "  World:   $world_name ($world_size)"
    echo "  Online:  $player_count players"
    echo "  Process: $pid"
    echo "  Uptime:  $uptime"
    echo "  CPU:     ${cpu_usage}%"
    echo "  Memory:  $mem_usage"
    return 0
  else
    echo "  Hytale server is not running"
    return 1
  fi
}


# ------------
# Hytale Check
# Check current and latest Hytale version
HytaleCheck() {
  echo "  Note: Hytale server downloads are not yet automated."
  echo "  Please visit hytale.com to download the latest server version."
  echo "  Place the server jar in: $working_dir/"
}


# -------------
# Hytale Update
# Download and install latest Hytale version
HytaleUpdate() {
  echo "  Note: Hytale server downloads are not yet automated."
  echo "  Please visit hytale.com to download the latest server version."
  echo "  Place the server jar in: $working_dir/"
}


# -----------
# Hytale Tail
# Display last 15 lines of log with errors highlighted in red
HytaleTail() {
  [ -f "$hytale_log" ] || { red "Log file not found: $hytale_log"; return 1; }
  tail -n 15 "$hytale_log" | while IFS= read -r line; do
    echo "$line" | grep -qi "error\|fail\|exception\|fatal\|critical\|warn" && red "$line" || echo "$line"
  done
}


# --------------
# Hytale Console
# Open the Screen session
HytaleConsole() {
  if ! screen -list | grep -q "hytale"; then
    echo "  Hytale server is not running"
    return 1
  fi
  echo "  Attaching to Hytale console"
  echo "  To detach press $(blue "Ctrl+A, then D")"
  echo ""
  sleep 3
  screen -r hytale
}


# -------------
# Hytale Backup
# Create a timestamped backup of the world file
# Keep last 4 weeks of backups plus any backup from the 1st of each month
HytaleBackup() {
  if [ ! -d "$hytale_universe" ]; then
    red "World directory not found: $hytale_universe"
    return 1
  fi
  mkdir -p "$backup_dir"
  local timestamp=$(date +%Y-%m-%d)
  local world_name=$(basename "$hytale_universe")
  local backup_file="$backup_dir/${timestamp}-${world_name}.tar.gz"
  echo "  Stopping Hytale server for backup"
  HytaleStop
  sleep 2
  echo "  Creating backup of world directory"
  tar -czf "$backup_file" -C "$(dirname "$hytale_universe")" "$world_name"
  if [ -f "$backup_file" ]; then
    echo "  Backup saved to: $backup_file"
    local size=$(du -h "$backup_file" | cut -f1)
    echo "  Backup size: $size"
    # Clean up old backups (keep last 4 weeks + first of month)
    # Only process backups for the current world (matches *-${world_name}.tar.gz)
    echo "  Cleaning up old backups"
    local cutoff_date=$(date -d "28 days ago" +%Y-%m-%d)
    local deleted_count=0
    for backup in "$backup_dir"/*-${world_name}.tar.gz; do
      [ -f "$backup" ] || continue
      local backup_name=$(basename "$backup")
      # Extract date (first 10 chars: YYYY-MM-DD)
      # Keep if it's the first of the month or newer than 28 days
      local backup_date="${backup_name:0:10}"
      local backup_day="${backup_date##*-}"
      if [ "$backup_day" = "01" ] || [ "$backup_date" \> "$cutoff_date" ] || [ "$backup_date" = "$cutoff_date" ]; then
        continue
      fi
      # Delete old backup
      rm -f "$backup"
      ((deleted_count++))
    done
    return 0
  else
    red "Failed to create backup"
    return 1
  fi
}


# -----
# Usage
# Display usage information
Usage() {
  echo "Hytale Commander"
  echo "Usage: $0 [cmd]"
  echo ""
  echo "  $(blue "backup")    create a backup of the world file"
  echo "  $(blue "check")     check current and latest version"
  echo "  $(blue "console")   open the console logs"
  echo "  $(blue "restart")   restart the server"
  echo "  $(blue "start")     start the server"
  echo "  $(blue "status")    check if the server is running"
  echo "  $(blue "stop")      stop the server"
  echo "  $(blue "tail")      tail the latest logs"
  echo "  $(blue "update")    update to the latest version"
}


# ----
# Main
for i in "$1"
do
  echo ""
  case $i in
		backup) HytaleBackup;;
		check) HytaleCheck;;
    update) HytaleUpdate;;
		start) HytaleStart;;
		stop) HytaleStop;;
		restart) HytaleRestart;;
		status) HytaleStatus;;
		tail) HytaleTail;;
		console) HytaleConsole;;
  *) Usage;;
  esac
  echo ""
done
