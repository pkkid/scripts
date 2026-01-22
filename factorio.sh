#!/bin/bash
# ======================================================================
# Factorio Commander
# A command-line tool for managing a Factorio headless server.
#
# Usage: factorio.sh [command]
#
# Commands:
#   backup    - Create a timestamped backup of the world file
#   check     - Check current and latest Factorio version
#   console   - Attach to the Factorio server console
#   cpmods    - Copy mods from Steam directory to server
#   restart   - Restart the Factorio server
#   start     - Start the Factorio server
#   status    - Check if the server is running
#   stop      - Stop the Factorio server
#   tail      - Display last 15 lines of logs (errors highlighted)
#   update    - Download and install latest Factorio version
#
# Written 2025-12-03 on Fedora 43 for Factorio v2.0.72
# ======================================================================

update_dir="$HOME/Sources"
working_dir="$HOME/Sources/factorio"
steam_dir="$HOME/.factorio"
backup_dir="/media/Synology/Michael/Backup/Factorio"
factorio_world="$working_dir/saves/PKsWaterWorldMK2.zip"

factorio="$working_dir/bin/x64/factorio"
factorio_log="$working_dir/factorio-current.log"
cd $working_dir || exit
mkdir -p $working_dir/mods/
mkdir -p $steam_dir/mods/


# ------
# Colors
# Output text in color
red() { echo -e "\033[38;2;251;73;52m$*\033[0m"; }
blue() { echo -e "\033[38;2;166;173;232m$*\033[0m"; }
dark() { echo -e "\033[38;2;30;30;30m$*\033[0m"; }


# --------------
# Factorio Start
# Start the Factorio server in a detached screen session
# Wait for server to start (check log for success message)
FactorioStart() {
  if screen -list | grep -q "factorio"; then
    echo "  Factorio server is already running"
    return 1
  fi
  rm -f "$factorio_log"
  echo "  Starting Factorio server"
  screen -dmS factorio $factorio --start-server "$factorio_world" --console-log "$factorio_log"
  local elapsed=0 timeout=30
  while [ $elapsed -lt $timeout ]; do
    if [ -f "$factorio_log" ]; then
      if grep -q "changing state from(CreatingGame) to(InGame)" "$factorio_log" 2>/dev/null; then
        echo "  Factorio server started successfully in screen session 'factorio'"
        return 0
      fi
      if grep -qi "error\|failed" "$factorio_log" 2>/dev/null; then
        red "Factorio server failed to start"
        echo ""; FactorioTail
        return 1
      fi
    fi
    sleep 1
    ((elapsed++))
  done
  echo "  Timeout waiting for server startup confirmation"
  echo ""; FactorioTail
  return 1
}


# -------------
# Factorio Stop
# Stop the Factorio server.
# Wait for graceful shutdown, then force kill if necessary
FactorioStop() {
  if ! screen -list | grep -q "factorio"; then
    echo "  Factorio server is not running"
    return 1
  fi
  echo "  Stopping Factorio server"
  screen -S factorio -X stuff "/quit$(printf '\r')"
  local elapsed=0 timeout=10
  while [ $elapsed -lt $timeout ]; do
    if ! screen -list | grep -q "factorio"; then
      echo "  Factorio server stopped successfully"
      return 0
    fi
    sleep 1
    ((elapsed++))
  done
  echo "  Server didn't stop gracefully, forcing shutdown"
  screen -S factorio -X quit
  echo "  Factorio server stopped"
}


# ----------------
# Factorio Restart
# Restart the Factorio server
FactorioRestart() {
  FactorioStop
  sleep 2
  FactorioStart
}


# ---------------
# Factorio Status
# Check if the Factorio server is running
FactorioStatus() {
  if screen -list | grep -q "factorio"; then
    local world_name=$(basename "$factorio_world" .zip)
    local world_size=$(du -h "$factorio_world" 2>/dev/null | cut -f1)
    local pid=$(pgrep -f "^/.*/factorio.*--start-server" | head -1)
    local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    local cpu_raw=$(ps -o %cpu= -p "$pid" 2>/dev/null | tr -d ' ')
    local cpu_cores=$(nproc)
    local cpu_usage=$(echo "$cpu_raw $cpu_cores" | awk '{printf "%.1f", $1/$2}')
    local mem_usage=$(ps -o rss= -p "$pid" 2>/dev/null | numfmt --to=iec --from-unit=1024)
    # Check for online players
    # Send /players command to server and capture console output
    local screen_output="/tmp/factorio-screen-$$.txt"
    screen -S factorio -X stuff "/players online$(printf '\r')"
    sleep 0.5
    screen -S factorio -X hardcopy "$screen_output"
    local player_count=$(grep -oP 'Online players \(\K\d+(?=\))' "$screen_output" 2>/dev/null | tail -1)
    [ -z "$player_count" ] && player_count="0"
    rm -f "$screen_output"
    # Print the status
    echo "  World:   $world_name ($world_size)"
    echo "  Online:  $player_count players"
    echo "  Process: $pid Running"
    echo "  Uptime:  $uptime"
    echo "  CPU:     ${cpu_usage}%"
    echo "  Memory:  $mem_usage"
    return 0
  else
    echo "  Factorio server is not running"
    return 1
  fi
}


# --------------
# Factorio Check
# Check current and latest Factorio version
FactorioCheck() {
  url="https://www.factorio.com/get-download/latest/headless/linux64"
  version_latest_url=$(curl -sI "$url" | grep -i "^location:" | awk '{print $2}' | tr -d '\r')
  version_latest_filename=$(basename "$version_latest_url" | cut -d '?' -f 1)
  version_latest=$(echo "$version_latest_filename" | sed 's/factorio-headless_linux_//g' | sed 's/.tar.gz//g' | sed 's/.tar.xz//g')
  update_file="$update_dir/$version_latest_filename"
  version_current="Not installed"
  if [ -f "$factorio" ]; then
    version_current=$($factorio --version | grep "Version: " | head -1 | awk '{print $2}')
  fi
  echo "  Latest version:  $(blue "$version_latest") $(dark $version_latest_filename)"
  echo "  Current version: $(blue "$version_current") $(dark $factorio)"
  echo "  Installed mods:         $(dark "$working_dir/mods/")"
  for mod in $working_dir/mods/*.zip; do
    if [ -f "$mod" ]; then
      echo "   • $(basename "$mod")"
    fi
  done
}


# ------------------
# Factorio Copy Mods
# Copy mods from Steam directory to server directory
FactorioCopyMods() {
  echo "  Removing current mods in $working_dir/mods/"
  rm -f $working_dir/mods/*.zip 2>/dev/null
  echo "  Copying mods from $steam_dir/mods/"
  for mod in $steam_dir/mods/*.zip; do
    if [ -f "$mod" ]; then
      echo "  • $(basename "$mod")"
      cp "$mod" $working_dir/mods/
    fi
  done
  echo "  Mods should now match your Steam installation."
}


# ---------------
# Factorio Update
# Download and install latest Factorio version
FactorioUpdate() {
  cd $update_dir
  FactorioCheck  # sets variables
  echo "  Downloading $version_latest_url"
  wget -qO "$update_file" "$url"
  echo "  Extracting $version_latest_filename"
  tar -xJf "$update_file"
  echo "  Factorio server should now be running $version_latest"
}


# -------------
# Factorio Tail
# Display last 15 lines of log with errors highlighted in red
FactorioTail() {
  [ -f "$factorio_log" ] || { red "Log file not found: $factorio_log"; return 1; }
  tail -n 15 "$factorio_log" | while IFS= read -r line; do
    echo "$line" | grep -qi "error\|fail\|exception\|fatal\|critical" && red "$line" || echo "$line"
  done
}


# ----------------
# Factorio Console
# Open the Screen session
FactorioConsole() {
  if ! screen -list | grep -q "factorio"; then
    echo "  Factorio server is not running"
    return 1
  fi
  echo "  Attaching to Factorio console"
  echo "  To detach press $(blue "Ctrl+A, then D")"
  echo ""
  sleep 3
  screen -r factorio
}


# ---------------
# Factorio Backup
# Create a timestamped backup of the world file
# Keep last 4 weeks of backups plus any backup from the 1st of each month
FactorioBackup() {
  if [ ! -f "$factorio_world" ]; then
    red "World file not found: $factorio_world"
    return 1
  fi
  mkdir -p "$backup_dir"
  local timestamp=$(date +%Y-%m-%d)
  local world_name=$(basename "$factorio_world" .zip)
  local backup_file="$backup_dir/${timestamp}-${world_name}.zip"
  echo "  Creating backup of world file"
  cp "$factorio_world" "$backup_file"
  if [ -f "$backup_file" ]; then
    echo "  Backup saved to: $backup_file"
    local size=$(du -h "$backup_file" | cut -f1)
    echo "  Backup size: $size"
    # Clean up old backups (keep last 4 weeks + first of month)
    # Only process backups for the current world (matches *-${world_name}.zip)
    echo "  Cleaning up old backups"
    local cutoff_date=$(date -d "28 days ago" +%Y-%m-%d)
    local deleted_count=0
    for backup in "$backup_dir"/*-${world_name}.zip; do
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
  echo "Factorio Commander"
  echo "Usage: $0 [cmd]"
  echo ""
  echo "  $(blue "backup")    create a backup of the world file"
  echo "  $(blue "check")     check current and latest version"
  echo "  $(blue "console")   open the console logs"
  echo "  $(blue "cpmods")    copy mods from steam install"
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
		backup) FactorioBackup;;
		check) FactorioCheck;;
    cpmods) FactorioCopyMods;;
    update) FactorioUpdate;;
		start) FactorioStart;;
		stop) FactorioStop;;
		restart) FactorioRestart;;
		status) FactorioStatus;;
		tail) FactorioTail;;
		console) FactorioConsole;;
  *) Usage;;
  esac
  echo ""
done
