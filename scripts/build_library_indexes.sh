#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$HOME/LZ/genome-library/indexes"
GENOMES="$HOME/LZ/genomes"
SKANI="$HOME/miniconda3/envs/skani/bin/skani"
LOG_DIR="$HOME/LZ/genome-library/logs"
mkdir -p "$ROOT" "$LOG_DIR"
exec 9>"$ROOT/.build.lock"
if ! flock -n 9; then
  echo "Another library index build is running" >&2
  exit 75
fi
exec > >(tee -a "$LOG_DIR/build.log") 2>&1
log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*"; }
trap 'status=$?; log "LIBRARY_INDEX_FAILED exit_code=$status"; exit $status' ERR

log "INDEX_DRIVER_STARTED pid=$$"
while [[ ! -f "$HOME/LZ/ani-skani/PIPELINE_COMPLETE" ]]; do sleep 60; done
while [[ ! -f "$HOME/LZ/ani-skani/Staphylococcus_aureus_PIPELINE_COMPLETE" ]]; do sleep 60; done
log "PRIOR_ANI_COMPLETE"

exec 8>"$HOME/LZ/.benchmark_compute.lock"
log "WAITING_FOR_COMPUTE_LOCK"
flock 8
log "COMPUTE_LOCK_ACQUIRED"

build_one() {
  local species=$1 expected=$2
  local dir="$ROOT/$species"
  local list="$ROOT/$species.genomes.list"
  if [[ -f "$dir/READY" ]]; then
    log "INDEX_ALREADY_READY species=$species"
    return
  fi
  if [[ -e "$dir" ]]; then
    local backup="$ROOT/.${species}.incomplete.$(date +%s)"
    log "MOVE_INCOMPLETE_INDEX species=$species backup=$backup"
    mv "$dir" "$backup"
  fi
  find "$GENOMES/$species" -maxdepth 1 -type f -print | sort > "$list"
  local count
  count=$(wc -l < "$list")
  [[ "$count" -eq "$expected" ]] || { log "INDEX_COUNT_ERROR species=$species count=$count expected=$expected"; exit 1; }
  log "INDEX_BUILD_START species=$species count=$count"
  /usr/bin/time -v "$SKANI" sketch -t 16 -l "$list" -o "$dir" > "$LOG_DIR/$species.log" 2>&1
  for required in sketches.db2 index.db2 markers.bin2 README.txt; do
    [[ -f "$dir/$required" ]] || { log "INDEX_FILE_MISSING species=$species file=$required"; exit 1; }
  done
  printf '%s\n' "$($SKANI --version)" > "$dir/VERSION"
  touch "$dir/READY"
  log "INDEX_BUILD_COMPLETE species=$species"
}

build_one Bifidobacterium_breve 335
build_one Bifidobacterium_longum 1123
build_one Escherichia_coli 62560
build_one Staphylococcus_aureus 25171
touch "$ROOT/LIBRARY_READY"
log "LIBRARY_INDEX_COMPLETE"
