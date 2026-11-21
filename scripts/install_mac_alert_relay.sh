#!/bin/zsh
# Install the pipeline-alert relay on the founder's Mac (scripts/mac_alert_relay.py → ~/bin, launchd every 10 min).
# Re-run after changing the relay. Scripts live in ~/bin: launchd cannot run anything under ~/Documents (TCC).
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/bin/pipeline_alert_relay.py"
PLIST="$HOME/Library/LaunchAgents/com.wissam.pipeline-alerts.plist"
mkdir -p "$HOME/bin/logs" "$HOME/bin/state"
cp "$REPO_DIR/scripts/mac_alert_relay.py" "$DEST"
chmod 755 "$DEST"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>com.wissam.pipeline-alerts</string>
	<key>ProgramArguments</key>
	<array>
		<string>/usr/bin/python3</string>
		<string>$DEST</string>
	</array>
	<key>StartInterval</key>
	<integer>600</integer>
	<key>RunAtLoad</key>
	<true/>
	<key>StandardOutPath</key>
	<string>$HOME/bin/logs/pipeline_alerts.log</string>
	<key>StandardErrorPath</key>
	<string>$HOME/bin/logs/pipeline_alerts_error.log</string>
	<key>Umask</key>
	<integer>63</integer>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/com.wissam.pipeline-alerts" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed: $DEST, $PLIST"
