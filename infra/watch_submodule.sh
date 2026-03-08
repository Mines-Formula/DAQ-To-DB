#!/usr/bin/env bash
set -u

REPO_DIR="/home/mines_formula/data-to-db"
SUBMODULE_PATH="data/DBCFiles"
STATE_FILE="$REPO_DIR/infra/.submodule_head_last_seen"
LOG_FILE="$REPO_DIR/infra/submodule_watcher.log"
POLL_SECONDS=15

cd "$REPO_DIR" || exit 1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

get_local_head() {
    git -C "$REPO_DIR/$SUBMODULE_PATH" rev-parse HEAD 2>/dev/null
}
get_remote_head() {
    git -C "$REPO_DIR/$SUBMODULE_PATH" fetch origin main >/dev/null 2>&1
    git -C "$REPO_DIR/$SUBMODULE_PATH" rev-parse origin/main 2>/dev/null
}

current_head=$(get_local_head)
if [ -z "$current_head" ]; then
    log "Error: could no reach submodule HEAD on startup"
    exit 1
fi 

if [ ! -f "$STATE_FILE" ]; then
    echo "$current_head" > "$STATE_FILE"
    log "Initialized state with HEAD $current_head"
fi

log "Watcher Started"

while true; do
    remote_head=$(get_remote_head)

    if [ -z "$remote_head" ]; then
        log "Failed to read remote submodule HEAD, retrying in $POLL_SECONDS seconds"
        sleep "$POLL_SECONDS"
        continue
    fi

    last_head=$(cat "$STATE_FILE" 2>/dev/null)

    if [ "$remote_head" != "$last_head" ]; then
        log "Remote submodule HEAD changed: $last_head -> $remote_head"
        log "Pulling update to HEAD"
        if git -C "$REPO_DIR/$SUBMODULE_PATH" checkout main >> "$LOG_FILE" 2>&1 && \
            git -C "$REPO_DIR/$SUBMODULE_PATH" pull origin main >> "$LOG_FILE" 2>&1; then
            echo "$remote_head" > "$STATE_FILE"
            log "Submodule pull completed successfully"
        else
            log "Submodule pull failed"
            sleep "$POLL_SECONDS"
            continue
        fi

        log "Running docker compose up --build -d"
        if docker compose -f "$REPO_DIR/docker-compose.yml" up --build -d >> "$LOG_FILE" 2>&1; then
            log "docker compose completed successfully"
        else
            log "docker compose failed"
        fi
    else
        log "watching"
    fi

    sleep "$POLL_SECONDS"
done