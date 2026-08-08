#!/usr/bin/env bash
#
# Deploy the current working tree to the Hugging Face Space.
#
# Pushes a single orphan commit containing only what the app needs at runtime.
# That matters for two reasons:
#
#   * The repo history carries data/products.csv (57 MB) and bfg.jar (14 MB) as
#     plain blobs, which the Hub rejects outright.
#   * The Hub also rejects binary files that are not in LFS/Xet, so images/ and
#     the analysis notebooks cannot be pushed as-is. The app does not use them.
#
# Your branch, working tree and GitHub remote are left untouched.
#
# Usage:
#   ./scripts/deploy_space.sh [space-url]

set -euo pipefail

SPACE_URL="${1:-https://huggingface.co/spaces/Krish264/NutriWeb}"
DEPLOY_BRANCH="_space_deploy_tmp"

cd "$(dirname "$0")/.."

# Paths the running app has no use for. Removed from the deploy commit only --
# they stay on disk and on your branch.
EXCLUDE=(images results tests scripts .devcontainer
         nutriweb/__pycache__ Limitations.md)

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "You have uncommitted changes. Commit them first so the deploy"
    echo "matches your branch:"
    git status --short
    exit 1
fi

ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Deploying '$ORIGINAL_BRANCH' -> $SPACE_URL"

# Always return to the original branch, even on failure.
cleanup() {
    git checkout -f "$ORIGINAL_BRANCH" --quiet 2>/dev/null || true
    git branch -D "$DEPLOY_BRANCH" --quiet 2>/dev/null || true
}
trap cleanup EXIT

git remote get-url space >/dev/null 2>&1 || git remote add space "$SPACE_URL"
git remote set-url space "$SPACE_URL"

git branch -D "$DEPLOY_BRANCH" --quiet 2>/dev/null || true
git checkout --orphan "$DEPLOY_BRANCH" --quiet
git add -A

for path in "${EXCLUDE[@]}"; do
    git rm -r --cached --quiet --ignore-unmatch "$path" >/dev/null 2>&1 || true
done
git rm --cached --quiet --ignore-unmatch ./*.html ./*.ipynb >/dev/null 2>&1 || true

# Refuse to push anything the Hub will reject, rather than discovering it in
# the middle of an upload.
oversized=$(git ls-files -z | xargs -0 ls -l 2>/dev/null \
            | awk '$5 > 10000000 {print $9}' || true)
if [[ -n "$oversized" ]]; then
    echo "Refusing to deploy: files over 10 MB would be rejected by the Hub:"
    echo "$oversized"
    exit 1
fi

binaries=$(git ls-files -z | xargs -0 file --mime 2>/dev/null \
           | grep -vE "text/|inode/|application/json" | cut -d: -f1 || true)
if [[ -n "$binaries" ]]; then
    echo "Refusing to deploy: binary files require LFS/Xet on the Hub:"
    echo "$binaries"
    exit 1
fi

for required in app.py styles.css requirements.txt README.md \
                pipeline/config.py data/additives.json; do
    git ls-files --error-unmatch "$required" >/dev/null 2>&1 || {
        echo "Refusing to deploy: $required is missing from the commit."
        exit 1
    }
done

echo "Deploying $(git ls-files | wc -l | tr -d ' ') files..."
git commit --quiet -m "Deploy: $(git log "$ORIGINAL_BRANCH" -1 --pretty=%s)"
git push space "$DEPLOY_BRANCH:main" --force

echo
echo "Pushed. Watch the build at ${SPACE_URL}?logs=build"
echo "Remember these must be set in the Space settings:"
echo "  NUTRIWEB_CATALOG_REPO  (variable)"
echo "  MONGODB_URI            (secret, optional)"
