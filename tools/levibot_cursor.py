#!/usr/bin/env python3
"""
LeviBot Cursor — repo mimarisini tek geçişte çıkaran hafif CLI.
- Dosya ağacı + boyutlar
- Python import grafiği (top-N)
- FastAPI/Router endpoint envanteri
- JS/TS import'ları (üst seviye)
- Solidity (imports, contract isimleri)
- docker-compose hizmet isimleri
- Makefile target'ları
- package.json scripts + deps
- requirements/pyproject bağımlılıkları
- Git kısa özet (opsiyonel)
- Mermaid diyagramları (Markdown içinde)

Kütüphane bağımlılığı yok (standart kütüphane).
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

IGNORES_DEFAULT = [
    r"(^|/)\.git($|/)",
    r"(^|/)\.venv($|/)",
    r"(^|/)node_modules($|/)",
    r"(^|/)\.pytest_cache($|/)",
    r"(^|/)\.mypy_cache($|/)",
    r"(^|/)dist($|/)",
    r"(^|/)build($|/)",
    r"(^|/)\.next($|/)",
    r"(^|/)coverage($|/)",
    r"(^|/)artifacts($|/)",
    r"(^|/)data($|/)",
    r"(^|/)\.benchmarks($|/)",
    r"(^|/)\.cursor($|/)",
]

PY_EXT = {".py"}
JS_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx"}
SOL_EXT = {".sol"}


def matches_ignore(p: Path, ignore_patterns):
    s = str(p)
    return any(re.search(pat, s) for pat in ignore_patterns)


def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"


def tree_lines(root: Path, ignore_patterns):
    lines = []

    def walk(dirp: Path, prefix=""):
        entries = []
        for e in dirp.iterdir():
            if matches_ignore(e, ignore_patterns):
                continue
            entries.append(e)
        entries = sorted(entries, key=lambda x: (not x.is_dir(), x.name.lower()))
        for i, e in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            if e.is_dir():
                lines.append(f"{prefix}{connector}{e.name}/")
                walk(e, prefix + ("    " if last else "│   "))
            else:
                try:
                    sz = e.stat().st_size
                    lines.append(f"{prefix}{connector}{e.name} ({human_size(sz)})")
                except Exception:
                    lines.append(f"{prefix}{connector}{e.name}")

    walk(root)
    return lines


# ---------- Python import graph & FastAPI routes ----------
class PyFileInfo(ast.NodeVisitor):
    def __init__(self):
        self.imports = []  # list of module names
        self.fastapi_routes = []  # tuples (method, path, funcname)
        self.app_vars = set()  # variables that may be FastAPI/Router instances

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name:
                self.imports.append(alias.name.split(".")[0])

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module.split(".")[0])

    def visit_Assign(self, node):
        # Detect FastAPI()/APIRouter() simple patterns
        try:
            if isinstance(node.value, ast.Call) and isinstance(
                node.value.func, ast.Name
            ):
                if node.value.func.id in {"FastAPI", "APIRouter"}:
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            self.app_vars.add(t.id)
        except Exception:
            pass
        self.generic_visit(node)

    def visit_Call(self, node):
        # Detect decorator or call like router.get("/path") or app.post(...)
        # method candidates:
        methods = {"get", "post", "put", "delete", "patch", "options", "head"}
        try:
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr in methods:
                    # owner could be a Name (router/app) or Attribute
                    owner = None
                    if isinstance(node.func.value, ast.Name):
                        owner = node.func.value.id
                    if owner in self.app_vars or owner in {
                        "app",
                        "router",
                        "api",
                        "r",
                        "v1",
                        "v2",
                    }:
                        path = None
                        if node.args and isinstance(
                            node.args[0], (ast.Str, ast.Constant)
                        ):
                            path = getattr(node.args[0], "s", None) or getattr(
                                node.args[0], "value", None
                            )
                        self.fastapi_routes.append((attr.upper(), path or "<?>"))
        except Exception:
            pass
        self.generic_visit(node)


def parse_python_file(p: Path):
    try:
        src = p.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
        v = PyFileInfo()
        v.visit(tree)
        # Function names for routes (best-effort via previous decorator context would be heavy; skip)
        return v.imports, v.fastapi_routes
    except Exception:
        return [], []


# ---------- JS/TS imports ----------
JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\))"""
)


def parse_js_imports(p: Path):
    try:
        s = p.read_text(encoding="utf-8", errors="ignore")
        mods = []
        for m in JS_IMPORT_RE.finditer(s):
            mod = m.group(1) or m.group(2)
            if mod and not mod.startswith((".", "/")):
                mods.append(mod.split("/")[0])  # top-level package
        return mods
    except Exception:
        return []


# ---------- Solidity ----------
SOL_IMPORT_RE = re.compile(r'^\s*import\s+["\']([^"\']+)["\'];', re.MULTILINE)
SOL_CONTRACT_RE = re.compile(r"contract\s+([A-Za-z_]\w*)")


def parse_solidity(p: Path):
    try:
        s = p.read_text(encoding="utf-8", errors="ignore")
        imports = SOL_IMPORT_RE.findall(s)
        contracts = SOL_CONTRACT_RE.findall(s)
        return imports, contracts
    except Exception:
        return [], []


# ---------- docker-compose ----------
def parse_compose_services(compose_path: Path):
    try:
        txt = compose_path.read_text(encoding="utf-8", errors="ignore")
        services = []
        in_services = False
        indent_level = None
        for line in txt.splitlines():
            if re.match(r"^\s*services\s*:\s*$", line):
                in_services = True
                indent_level = None
                continue
            if in_services:
                if re.match(r"^\S", line):  # back to top-level
                    break
                m = re.match(r"^(\s+)([A-Za-z0-9_.-]+)\s*:\s*$", line)
                if m:
                    if indent_level is None:
                        indent_level = len(m.group(1))
                    elif len(m.group(1)) < indent_level:
                        break
                    services.append(m.group(2))
        return services
    except Exception:
        return []


# ---------- Makefile ----------
def parse_make_targets(make_path: Path):
    try:
        tgt = []
        for line in make_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(?:.+)?$", line)
            if m and not m.group(1).startswith((".", "#", " ")):
                tgt.append(m.group(1))
        return sorted(list(set(tgt)))
    except Exception:
        return []


# ---------- package.json ----------
def parse_package_json(p: Path):
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        scripts = list((data.get("scripts") or {}).keys())
        deps = list((data.get("dependencies") or {}).keys())
        devdeps = list((data.get("devDependencies") or {}).keys())
        return scripts, deps, devdeps
    except Exception:
        return [], [], []


# ---------- requirements / pyproject ----------
def parse_requirements(p: Path):
    try:
        pkgs = []
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[<>=!~]", line)[0].strip()
            if name:
                pkgs.append(name)
        return pkgs
    except Exception:
        return []


def parse_pyproject(p: Path):
    try:
        s = p.read_text(encoding="utf-8", errors="ignore")
        # very lightweight parse for dependencies in pyproject.toml
        deps = re.findall(
            r'^\s*["\']?([A-Za-z0-9_.\-]+)["\']?\s*(?:=|>|<|~|!|,|\])',
            s,
            flags=re.MULTILINE,
        )
        return list(sorted(set(deps)))
    except Exception:
        return []


# ---------- git summary ----------
def git_summary(root: Path, limit=10):
    try:

        def run(*args):
            return (
                subprocess.check_output(args, cwd=str(root))
                .decode("utf-8", "ignore")
                .strip()
            )

        rev = run("git", "rev-parse", "--short", "HEAD")
        shortlog = run("git", "log", "--pretty=%h %ad %s", "--date=short", f"-n{limit}")
        return rev, shortlog
    except Exception:
        return None, None


# ---------- main scan ----------
def scan_repo(root: Path, ignore_patterns, top_n_edges=30):
    files = []
    py_import_edges = Counter()
    js_imports = Counter()
    fastapi_routes = []
    sol_imports = []
    sol_contracts = []
    compose_services = []
    make_targets = []
    pkg_scripts, pkg_deps, pkg_devdeps = [], [], []
    reqs = []
    pyproj = []
    total_bytes = 0

    # locate special files
    compose_path = None
    make_path = None
    pkg_json_path = None
    req_path = None
    pyproject_path = None

    for dirpath, dirnames, filenames in os.walk(root):
        dirp = Path(dirpath)
        # prune ignores
        dirnames[:] = [
            d for d in dirnames if not matches_ignore(dirp / d, ignore_patterns)
        ]
        for fn in filenames:
            p = dirp / fn
            if matches_ignore(p, ignore_patterns):
                continue
            files.append(p)
            try:
                total_bytes += p.stat().st_size
            except Exception:
                pass
            # special paths
            lname = fn.lower()
            if lname in ("docker-compose.yml", "docker-compose.yaml"):
                compose_path = p
            elif lname == "makefile":
                make_path = p
            elif lname == "package.json":
                pkg_json_path = p
            elif lname in ("requirements.txt", "requirements-prod.txt"):
                # prefer prod later but collect one
                if req_path is None or lname == "requirements-prod.txt":
                    req_path = p
            elif lname == "pyproject.toml":
                pyproject_path = p

            # parse language-specific
            ext = p.suffix.lower()
            if ext in PY_EXT:
                mods, routes = parse_python_file(p)
                for m in mods:
                    py_import_edges[(p.name, m)] += 1
                fastapi_routes.extend([(p.name, m, path) for (m, path) in routes])
            elif ext in JS_EXT:
                for m in parse_js_imports(p):
                    js_imports[m] += 1
            elif ext in SOL_EXT:
                imps, cons = parse_solidity(p)
                if imps:
                    sol_imports.extend(imps)
                if cons:
                    sol_contracts.extend(cons)

    if compose_path:
        compose_services = parse_compose_services(compose_path)
    if make_path:
        make_targets = parse_make_targets(make_path)
    if pkg_json_path:
        pkg_scripts, pkg_deps, pkg_devdeps = parse_package_json(pkg_json_path)
    if req_path:
        reqs = parse_requirements(req_path)
    if pyproject_path:
        pyproj = parse_pyproject(pyproject_path)

    # Build Mermaid snippets
    tree_txt = "\n".join(tree_lines(root, ignore_patterns))
    edges_top = py_import_edges.most_common(top_n_edges)
    mermaid_import = (
        "graph TD\n"
        + "\n".join(f'  "{src}" --> "{dst}"' for ((src, dst), _) in edges_top)
        if edges_top
        else "graph TD\n  A[No Python imports found]-->B[OK]"
    )

    mermaid_services = None
    if compose_services:
        mermaid_services = (
            "flowchart LR\n  subgraph docker-compose\n"
            + "\n".join([f"    {s}([{s}])" for s in compose_services])
            + "\n  end"
        )

    # Git
    head, shortlog = git_summary(root)

    summary = {
        "files_count": len(files),
        "size_total": human_size(total_bytes),
        "py_edges_top": edges_top[:10],
        "js_imports_top": js_imports.most_common(10),
        "fastapi_routes_count": len(fastapi_routes),
        "sol_contracts": sorted(set(sol_contracts)),
        "compose_services": compose_services,
        "make_targets": make_targets,
        "pkg_scripts": pkg_scripts,
        "requirements_count": len(reqs) or len(pyproj),
    }

    report = []
    report.append("# LeviBot Architecture Report\n")
    report.append(f"- Repo: `{root}`")
    report.append(
        f"- Files: **{summary['files_count']}**, Size: **{summary['size_total']}**"
    )
    if head:
        report.append(f"- Git HEAD: `{head}`\n")
    # Tree
    report.append("## Tree\n")
    report.append("```text\n" + tree_txt + "\n```\n")

    # Python imports
    report.append("## Python Import Graph (top edges)\n")
    report.append("```mermaid\n" + mermaid_import + "\n```\n")

    # FastAPI routes
    if fastapi_routes:
        report.append("## FastAPI / Router Endpoints (best-effort)\n")
        report.append("| File | Method | Path |")
        report.append("|---|---|---|")
        for fname, method, path in sorted(fastapi_routes):
            report.append(f"| `{fname}` | `{method}` | `{path}` |")
        report.append("")

    # JS/TS imports
    if js_imports:
        report.append("## JS/TS External Imports (top)\n")
        for name, cnt in js_imports.most_common(20):
            report.append(f"- {name} ×{cnt}")
        report.append("")

    # Solidity
    if sol_contracts or sol_imports:
        report.append("## Solidity\n")
        if sol_contracts:
            report.append("**Contracts:** " + ", ".join(sorted(set(sol_contracts))))
        if sol_imports:
            imps = Counter(sol_imports)
            report.append(
                "**Imports (top):** "
                + ", ".join(f"{k}×{v}" for k, v in imps.most_common(10))
            )
        report.append("")

    # docker-compose
    if compose_services:
        report.append("## docker-compose Services\n")
        report.append("```mermaid\n" + mermaid_services + "\n```\n")
        report.append("- Services: " + ", ".join(compose_services) + "\n")

    # Makefile
    if make_targets:
        report.append("## Makefile Targets\n")
        report.append(", ".join(make_targets) + "\n")

    # package.json
    if pkg_scripts or pkg_deps or pkg_devdeps:
        report.append("## package.json\n")
        if pkg_scripts:
            report.append("**Scripts:** " + ", ".join(pkg_scripts))
        if pkg_deps:
            report.append(
                "**Deps:** "
                + ", ".join(sorted(pkg_deps)[:20])
                + (" ..." if len(pkg_deps) > 20 else "")
            )
        if pkg_devdeps:
            report.append(
                "**DevDeps:** "
                + ", ".join(sorted(pkg_devdeps)[:20])
                + (" ..." if len(pkg_devdeps) > 20 else "")
            )
        report.append("")

    # Python deps
    if reqs or pyproj:
        report.append("## Python Dependencies\n")
        if reqs:
            report.append(
                ", ".join(sorted(set(reqs))[:40]) + (" ..." if len(reqs) > 40 else "")
            )
        elif pyproj:
            report.append(", ".join(pyproj[:40]) + (" ..." if len(pyproj) > 40 else ""))
        report.append("")

    # Git log
    if shortlog:
        report.append("## Git (last commits)\n")
        report.append("```text\n" + shortlog + "\n```\n")

    report.append("\n---\n")
    report.append(
        "_Generated by LeviBot Cursor — zero-deps. Mermaid diagrams render on GitHub._\n"
    )

    return "\n".join(report), summary


def main():
    ap = argparse.ArgumentParser(description="LeviBot Cursor — repo mimarisini çıkar")
    ap.add_argument("--repo", type=str, default=".", help="Repo kök dizini")
    ap.add_argument(
        "--out",
        type=str,
        default="architecture_report.md",
        help="Çıktı Markdown dosyası",
    )
    ap.add_argument(
        "--ignore",
        type=str,
        action="append",
        default=None,
        help="Regex ignore (çoklu verilebilir)",
    )
    ap.add_argument(
        "--edges", type=int, default=30, help="Python import graph top-N edge"
    )
    args = ap.parse_args()

    root = Path(args.repo).resolve()
    if not root.exists():
        print(f"[ERR] Repo bulunamadı: {root}", file=sys.stderr)
        sys.exit(1)

    ignores = args.ignore if args.ignore else IGNORES_DEFAULT
    report, summary = scan_repo(root, ignores, top_n_edges=args.edges)
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"[OK] {args.out} yazıldı.")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
