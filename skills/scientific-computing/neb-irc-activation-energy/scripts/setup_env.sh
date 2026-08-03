#!/usr/bin/env bash
# Install GFN2-xTB and pysisyphus without conda or a Fortran compiler.
# Usage:  bash setup_env.sh   then   source "$ROOT/env.sh"
#
# xtb ships prebuilt Linux x86_64 binaries on GitHub releases (no compiler needed).
# pysisyphus installs from PyPI. Neither route needs conda-forge, so this works in
# minimal or network-restricted environments where ORCA/Psi4/CREST are unavailable.
# Runs in 2-3 minutes. Re-run per session if the filesystem does not persist.
set -euo pipefail

# Some sandboxes leave HOME unset; guard it so `set -u` does not abort here, and
# so pip has a cache dir to write to.
export HOME="${HOME:-/tmp}"
ROOT="${ROOT:-$HOME/xtbenv}"        # override with ROOT=/path bash setup_env.sh
XTB_VERSION="${XTB_VERSION:-6.7.1}"
mkdir -p "$ROOT" && cd "$ROOT"

if [ ! -d xtb-dist ]; then
  echo "fetching xtb ${XTB_VERSION} ..."
  curl -sfL -o xtb.tar.xz \
    "https://github.com/grimme-lab/xtb/releases/download/v${XTB_VERSION}/xtb-${XTB_VERSION}-linux-x86_64.tar.xz"
  tar xf xtb.tar.xz && rm xtb.tar.xz
  mv "xtb-${XTB_VERSION}" xtb-dist 2>/dev/null || true
fi

python3 -c "import pysisyphus" 2>/dev/null || pip install --quiet --break-system-packages pysisyphus

cat > "$ROOT/env.sh" <<EOF
export XTBHOME=$ROOT/xtb-dist
export PATH=\$XTBHOME/bin:\$PATH
export LD_LIBRARY_PATH=\$XTBHOME/lib:\${LD_LIBRARY_PATH:-}
export XTBPATH=\$XTBHOME/share/xtb
# Match to physical cores. On a single core keep this at 1: oversubscription
# makes xtb slower, not faster. xtb's parallel efficiency is modest, so gains
# taper off past a handful of cores.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}
export OMP_STACKSIZE=1G
EOF

# shellcheck disable=SC1091
source "$ROOT/env.sh"
echo "xtb: $(xtb --version 2>&1 | grep -ioP 'version \S+' | head -1)"
echo "pysisyphus: $(python3 -c 'from importlib.metadata import version; print(version("pysisyphus"))')"
echo
echo "run 'source $ROOT/env.sh' in every new shell"
