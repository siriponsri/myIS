#!/usr/bin/env bash
set -euo pipefail

root=${1:?isolated A4 remote root required}
case "$root" in
  /opt/myis/a4-goal001-*-a4x1) ;;
  *) echo "unsafe A4 remote root" >&2; exit 2 ;;
esac

chunk_bytes=67108864
# Three model jobs run concurrently, each with four ranges at a time.
parallelism=4
model_root="$root/rehydrated-models"
mkdir -p "$model_root"

download() {
  local arm=$1 repository=$2 revision=$3 bytes=$4 expected_sha=$5
  local dir="$model_root/$arm"
  local parts="$dir/parts"
  local target="$dir/model.safetensors"
  mkdir -p "$parts"
  local count=$(( (bytes + chunk_bytes - 1) / chunk_bytes ))
  local failed=0
  for ((index=0; index<count; index+=1)); do
    local start=$((index * chunk_bytes)) end=$((start + chunk_bytes - 1))
    (( end >= bytes )) && end=$((bytes - 1))
    local size=$((end - start + 1)) part
    printf -v part '%s/part-%03d' "$parts" "$index"
    if [[ -f "$part" && $(stat -c '%s' "$part") -eq $size ]]; then
      continue
    fi
    rm -f "$part" "$part.tmp"
    (
      curl --fail --location --retry 5 --retry-all-errors --range "$start-$end" \
        --output "$part.tmp" "https://huggingface.co/$repository/resolve/$revision/model.safetensors"
      test "$(stat -c '%s' "$part.tmp")" -eq "$size"
      mv "$part.tmp" "$part"
    ) &
    if (( (index + 1) % parallelism == 0 )); then
      wait || failed=1
    fi
  done
  wait || failed=1
  (( failed == 0 )) || return 1
  cat "$parts"/part-* > "$target.tmp"
  test "$(stat -c '%s' "$target.tmp")" -eq "$bytes"
  test "$(sha256sum "$target.tmp" | awk '{print $1}')" = "$expected_sha"
  mv "$target.tmp" "$target"
}

download ARM-03 datalyes/patembed-large 2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad 1378856808 234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482 &
pid03=$!
download ARM-04 Snowflake/snowflake-arctic-embed-m-v2.0 95c2741480856aa9666782eb4afe11959938017f 1221487872 3d80d4727ac8759fb8624b690697c053a3d1992120111dc4a71178e608c26604 &
pid04=$!
download ARM-05 Qwen/Qwen3-Embedding-0.6B 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 1191586416 0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd &
pid05=$!
wait "$pid03"
wait "$pid04"
wait "$pid05"

sha256sum "$model_root"/*/model.safetensors > "$root/receipts/public-model-rehydration.sha256"
