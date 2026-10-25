"""B4P A3.3 (M10 finding 6, 2026-10-26): env/install_env.sh takes a mirror per conda channel (CONDA_MIRROR_CONDA_FORGE / _BIOCONDA / _GUROBI;
an unset channel stays direct - no Chinese mirror carries the gurobi channel), keeps the earlier whole-prefix CONDA_MIRROR when no per-channel
variable is set, checks the first two package URLs of every replaced channel with a 1 KB curl range request before conda create (failure ->
MIRROR_CHECK_FAILED, exit 2, nothing downloaded), and offers `--check-mirrors` (checks only, no environment). Tests use a six-line explicit list,
a MOCK curl on PATH (reachable prefixes from MOCK_CURL_OK; no network), a fake conda that only records its arguments; one test serves two tiny
files from a local loopback http.server and uses the real curl (skipped without curl). Nothing is downloaded, no environment is created."""
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package/env"
ORIGIN = "https://conda.anaconda.org"
SAMPLE = """# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: linux-64
@EXPLICIT
https://conda.anaconda.org/conda-forge/linux-64/_libgcc_mutex-0.1-conda_forge.tar.bz2#d7c89558ba9fa0495403155b64376d81
https://conda.anaconda.org/conda-forge/linux-64/_openmp_mutex-4.5-2_gnu.tar.bz2#73aaf86a425cc6e73fcf236a5a46396d
https://conda.anaconda.org/bioconda/noarch/snakemake-minimal-7.32.4-pyhdfd78af_1.tar.bz2#9dea790fb457de73b4ced05ff42c196f
https://conda.anaconda.org/bioconda/noarch/snakemake-7.32.4-hdfd78af_1.tar.bz2#00000000000000000000000000000001
https://conda.anaconda.org/gurobi/linux-64/gurobi-12.0.3-py311_0.tar.bz2#5e871147ad11a71bb654e53dbf58ebe0
https://conda.anaconda.org/gurobi/linux-64/gurobi-12.0.2-py311_0.tar.bz2#00000000000000000000000000000002
"""
MOCK_CURL = """#!/bin/bash
# mock curl (tests only): the last argument is the URL; reachable when it starts with one of the space-separated prefixes in MOCK_CURL_OK
url=${@: -1}; echo "$*" >> "$MOCK_CURL_LOG"
for p in ${MOCK_CURL_OK:-}; do [[ "$url" == "$p"* ]] && exit 0; done
echo "curl: (22) The requested URL returned error: 404" >&2; exit 22
"""
FAKE_CONDA = """#!/bin/bash
# fake conda (tests only): records its arguments; `create -p <prefix>` makes <prefix>/bin/python that exits 0 (so the pip / env_check steps pass)
echo "$*" >> "$FAKE_CONDA_LOG"
[ "${1:-}" = --version ] && { echo "conda 0.0 (fake)"; exit 0; }
p=""; while [ $# -gt 0 ]; do case "$1" in -p) p=$2; shift 2;; *) shift;; esac; done
[ -n "$p" ] || exit 1
mkdir -p "$p/bin"; printf '#!/bin/bash\\nexit 0\\n' > "$p/bin/python"; chmod 755 "$p/bin/python"
"""


def _setup(tmp: Path) -> Path:
    env = tmp / "pkg" / "env"; env.mkdir(parents=True)
    shutil.copy(ENV / "install_env.sh", env / "install_env.sh")
    (env / "conda_explicit_linux64.txt").write_text(SAMPLE); (env / "pip_only.txt").write_text("currencyconverter==0.18.9\n")
    (env / "ENV_LOCK.txt").write_text("# Python 3.11.13\nnumpy==1.26.4\n"); (env / "env_check.py").write_text("import sys\nsys.exit(0)\n")
    b = tmp / "bin"; b.mkdir()
    for name, text in (("curl", MOCK_CURL), ("conda", FAKE_CONDA)):
        (b / name).write_text(text); (b / name).chmod(0o755)
    return env


def _run(tmp: Path, env: Path, args=(), extra=None, real_curl=False):
    e = {k: v for k, v in os.environ.items() if not k.startswith("CONDA_MIRROR") and k not in ("CONDA", "CONDA_PKGS_DIRS", "TMPDIR", "PIP_CACHE_DIR")}
    path = os.environ.get("PATH", "")
    e.update(PATH=(path if real_curl else f"{tmp / 'bin'}:{path}"), MOCK_CURL_LOG=str(tmp / "curl_calls.txt"), FAKE_CONDA_LOG=str(tmp / "conda_calls.txt"),
             CONDA=str(tmp / "bin" / "conda"), TMPDIR=str(tmp / "tmp"))
    e.update(extra or {})
    return subprocess.run(["bash", str(env / "install_env.sh"), *args], env=e, cwd=str(tmp), capture_output=True, text=True, timeout=300)


def _calls(tmp: Path, name: str) -> list:
    p = tmp / f"{name}_calls.txt"
    return p.read_text().splitlines() if p.exists() else []


def test_per_channel_mirror_replaces_only_that_channel(tmp_path):
    env = _setup(tmp_path); cf = "http://mirror.cf/anaconda/cloud/conda-forge"
    p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR_CONDA_FORGE": cf + "/", "MOCK_CURL_OK": "http://mirror.cf"})
    assert p.returncode == 0, p.stdout + p.stderr
    assert "MIRROR:conda-forge:" + cf in p.stdout and "DIRECT:bioconda:" in p.stdout and "DIRECT:gurobi:" in p.stdout and "MIRROR_OK:conda-forge:2 urls" in p.stdout
    assert "MIRROR_CHECK_DONE" in p.stdout and "MIRROR_OK:gurobi" not in p.stdout and "MIRROR_OK:bioconda" not in p.stdout
    lines = (env / ".explicit_mirror.txt").read_text().splitlines(); orig = SAMPLE.splitlines()
    assert lines[:4] == orig[:4] and len(lines) == len(orig)
    assert lines[4:6] == [x.replace(ORIGIN + "/conda-forge/", cf + "/") for x in orig[4:6]] and all(x.endswith(y.split("#")[-1]) for x, y in zip(lines[4:6], orig[4:6]))
    assert lines[6:] == orig[6:]                                                                                    # bioconda and gurobi stay direct
    calls = _calls(tmp_path, "curl")
    assert len(calls) == 2 and all("-r 0-1023" in c and "--max-time 20" in c and c.endswith(x.split("#")[0].replace(ORIGIN + "/conda-forge/", cf + "/")) for c, x in zip(calls, orig[4:6]))
    assert _calls(tmp_path, "conda") == [] and not (tmp_path / "pkg" / "tmp").exists()                                  # --check-mirrors: no conda, no environment


def test_whole_prefix_mirror_behaves_as_before(tmp_path):
    env = _setup(tmp_path); base = "http://mirror.all/anaconda/cloud"
    p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR": base, "MOCK_CURL_OK": "http://mirror.all"})
    assert p.returncode == 0, p.stdout + p.stderr
    assert (env / ".explicit_mirror.txt").read_text() == SAMPLE.replace(ORIGIN + "/", base + "/")                        # the earlier sed over the whole prefix
    assert all(f"MIRROR_OK:{c}:2 urls" in p.stdout for c in ("conda-forge", "bioconda", "gurobi")) and len(_calls(tmp_path, "curl")) == 6
    # per-channel variables win over the whole-prefix form: gurobi stays direct although CONDA_MIRROR is set
    p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR": base, "CONDA_MIRROR_CONDA_FORGE": base + "/conda-forge", "MOCK_CURL_OK": "http://mirror.all"})
    assert p.returncode == 0 and "DIRECT:gurobi:" in p.stdout and "DIRECT:bioconda:" in p.stdout and "MIRROR_OK:conda-forge" in p.stdout
    assert (env / ".explicit_mirror.txt").read_text().splitlines()[6:] == SAMPLE.splitlines()[6:]


def test_unreachable_mirror_stops_before_conda_create(tmp_path):
    env = _setup(tmp_path); gu = "http://mirror.nogurobi/cloud/gurobi"
    p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR_GUROBI": gu, "MOCK_CURL_OK": ""})
    assert p.returncode == 2 and f"MIRROR_CHECK_FAILED:gurobi:{gu}/linux-64/gurobi-12.0.3-py311_0.tar.bz2" in p.stdout and "MIRROR_OK" not in p.stdout
    # the install itself (no --check-mirrors): the check runs after INSTALL_START and before conda create; nothing is created
    prefix = tmp_path / "envprefix"
    p = _run(tmp_path, env, (str(prefix),), {"CONDA_MIRROR_CONDA_FORGE": "http://mirror.cf/conda-forge", "CONDA_MIRROR_GUROBI": gu, "MOCK_CURL_OK": "http://mirror.cf"})
    assert p.returncode == 2, p.stdout + p.stderr
    assert "MIRROR_OK:conda-forge" in p.stdout and f"MIRROR_CHECK_FAILED:gurobi:{gu}" in p.stdout and "nothing downloaded, no environment created" in p.stdout
    assert _calls(tmp_path, "conda") == ["--version"] and not prefix.exists()                                           # conda create never called
    log = next(env.glob("INSTALL_*.log")).read_text()
    assert "MIRROR_CHECK_FAILED:gurobi" in log and "CONDA_DONE" not in log


def test_reachable_mirror_runs_conda_create_with_the_mirrored_list(tmp_path):
    env = _setup(tmp_path); cf = "http://mirror.cf/anaconda/cloud/conda-forge"; prefix = tmp_path / "envprefix"
    p = _run(tmp_path, env, (str(prefix),), {"CONDA_MIRROR_CONDA_FORGE": cf, "MOCK_CURL_OK": "http://mirror.cf"})
    assert p.returncode == 0, p.stdout + p.stderr
    calls = _calls(tmp_path, "conda")
    assert calls == ["--version", f"create -y -p {prefix} --file {env / '.explicit_mirror.txt'}"] and (prefix / "bin" / "python").exists()
    assert "MIRROR_OK:conda-forge" in p.stdout and "CONDA_DONE" in p.stdout and "key_packages_identical=yes" in p.stdout
    # no mirror at all: direct list, no check, conda create with the original file
    env2 = _setup(tmp_path / "second"); prefix2 = tmp_path / "second" / "envprefix"
    p = _run(tmp_path / "second", env2, (str(prefix2),), {})
    assert p.returncode == 0, p.stdout + p.stderr
    assert "MIRROR_CHECK:none" in p.stdout and _calls(tmp_path / "second", "curl") == [] and _calls(tmp_path / "second", "conda")[1] == f"create -y -p {prefix2} --file {env2 / 'conda_explicit_linux64.txt'}"


def test_invalid_mirror_url_is_refused(tmp_path):
    env = _setup(tmp_path)
    p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR_BIOCONDA": "ftp://mirror.x/bioconda"})
    assert p.returncode == 2 and "MIRROR_URL_INVALID:bioconda:ftp://mirror.x/bioconda" in p.stdout and _calls(tmp_path, "curl") == []
    p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR_GUROBI": "https://mirror x/gurobi"})
    assert p.returncode == 2 and "MIRROR_URL_INVALID:gurobi" in p.stdout


@pytest.mark.skipif(shutil.which("curl") is None, reason="curl missing")
def test_real_curl_against_a_local_loopback_server(tmp_path):
    """the real curl range request against a loopback http.server that serves the two conda-forge package names (2 KB each); the bioconda channel
    points at a path the server does not have -> MIRROR_CHECK_FAILED."""
    env = _setup(tmp_path); www = tmp_path / "www" / "conda-forge" / "linux-64"; www.mkdir(parents=True)
    for name in ("_libgcc_mutex-0.1-conda_forge.tar.bz2", "_openmp_mutex-4.5-2_gnu.tar.bz2"):
        (www / name).write_bytes(b"x" * 2048)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(tmp_path / "www")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.5).close(); break
            except OSError:
                time.sleep(0.1)
        base = f"http://127.0.0.1:{port}"
        p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR_CONDA_FORGE": base + "/conda-forge"}, real_curl=True)
        assert p.returncode == 0 and "MIRROR_OK:conda-forge:2 urls" in p.stdout, p.stdout + p.stderr
        p = _run(tmp_path, env, ("--check-mirrors",), {"CONDA_MIRROR_CONDA_FORGE": base + "/conda-forge", "CONDA_MIRROR_BIOCONDA": base + "/missing"}, real_curl=True)
        assert p.returncode == 2 and "MIRROR_OK:conda-forge" in p.stdout and f"MIRROR_CHECK_FAILED:bioconda:{base}/missing/noarch/snakemake-minimal" in p.stdout, p.stdout
    finally:
        srv.terminate(); srv.wait(timeout=10)
