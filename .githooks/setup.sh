#!/bin/sh
# Run once in every clone of this repository: turns on the phone filter and the hooks.
#
#   .githooks/setup.sh                    # here, where the CV already has your real number
#   .githooks/setup.sh '+386 40 123 456'  # in a new clone: your number, to put back in the CV
#
# The number is kept in this clone's .git/config (cv.phone), which is never committed or pushed.
set -eu

cd "$(git rev-parse --show-toplevel)"
git config filter.cv-private.clean 'python3 -I .githooks/cv_filter.py clean'
git config filter.cv-private.smudge 'python3 -I .githooks/cv_filter.py smudge'
git config filter.cv-private.required true
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/post-commit .githooks/pre-push

[ $# -gt 0 ] && git config cv.phone "$1"

cv=$(ls ./*_CV.yaml 2>/dev/null | head -n 1)
[ -n "$cv" ] || exit 0
found=$(python3 -I .githooks/cv_filter.py phone < "$cv")
if [ -n "$found" ]; then
  git config cv.phone "$found"
elif git config --get cv.phone > /dev/null; then
  # a fresh clone holds the masked copy: check it out again so smudge puts the number back
  rm "$cv" && git checkout -- "$cv"
fi
echo "Phone filter and hooks are on. cv.phone = $(git config --get cv.phone || echo '(not set)')"
