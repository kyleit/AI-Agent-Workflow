#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    exit 1
}

for script in install.sh update.sh tools/validate-skills.sh; do
    if grep -nE 'head[[:space:]]+-n[[:space:]]+-1' "$script" >/dev/null; then
        fail "$script still uses non-portable head -n -1"
    fi
    if ! grep -Eq '(fm|frontmatter)=\$\(awk ' "$script"; then
        fail "$script does not use the portable awk extractor"
    fi
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

printf '%s\n' \
    '---' \
    'name: fixture' \
    'description: valid fixture' \
    '---' \
    '# body' > "$tmp_dir/valid.md"

frontmatter="$(awk 'NR > 1 { sub(/\r$/, ""); if ($0 == "---") exit; print }' "$tmp_dir/valid.md")"
grep -q '^name: fixture$' <<<"$frontmatter" || fail "valid fixture name was not extracted"
grep -q '^description: valid fixture$' <<<"$frontmatter" || fail "valid fixture description was not extracted"

printf '%s\n' \
    '---' \
    'description: malformed fixture' \
    '---' > "$tmp_dir/malformed.md"

frontmatter="$(awk 'NR > 1 { sub(/\r$/, ""); if ($0 == "---") exit; print }' "$tmp_dir/malformed.md")"
if grep -q '^name:' <<<"$frontmatter"; then
    fail "malformed fixture unexpectedly contained name"
fi

skill_count=0
for skill_md in skills/*/SKILL.md; do
    skill_count=$((skill_count + 1))
    frontmatter="$(awk 'NR > 1 { sub(/\r$/, ""); if ($0 == "---") exit; print }' "$skill_md")"
    grep -q '^name:' <<<"$frontmatter" || fail "$skill_md missing name"
    grep -q '^description:' <<<"$frontmatter" || fail "$skill_md missing description"
done

test "$skill_count" -eq 59 || fail "expected 59 canonical skills, found $skill_count"
printf 'PASS: portable SKILL.md frontmatter validation (%s skills)\n' "$skill_count"
