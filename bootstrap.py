#!/usr/bin/env python3
"""
bootstrap.py — Initialize a new project from agentic-starter.

Usage:
    python bootstrap.py --name "My Project" --author "Your Name"
    python bootstrap.py --name "My Project" --author "Your Name" --with-vector-db
    python bootstrap.py --name "My Project" --author "Your Name" --with-frontend

The bootstrap COPIES files from .templates/ into the project.
It never deletes template source files — re-running is always safe.
After installation, generates uv.lock for reproducible builds.
"""

import argparse
import subprocess
import shutil
from pathlib import Path

from cli.modules.frontend import FrontendModule

# ── Placeholders ──────────────────────────────────────────────────────────────

TEXT_EXTENSIONS = {
    ".py", ".md", ".toml", ".yml", ".yaml",
    ".json", ".env", ".txt", ".sh", ".ts", ".tsx"
}

VECTOR_DB_MANIFEST = {
    ".templates/vector-db/skills/qdrant": ".claude/skills/qdrant",
    ".templates/vector-db/skills/postgres": ".claude/skills/postgres",
    ".templates/vector-db/src/tools.py": "src/{{module}}/tools.py",
    ".templates/vector-db/src/agent.py": "src/{{module}}/agent.py",
    ".templates/vector-db/tests/test_tools.py": "tests/test_tools.py",
    ".templates/vector-db/docker-compose.yml": "docker-compose.yml",
}

_frontend_module = FrontendModule()

# ── Helpers ───────────────────────────────────────────────────────────────────

def replace_in_file(path: Path, replacements: dict[str, str]) -> None:
    try:
        content = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            content = content.replace(old, new)
        path.write_text(content, encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        pass


def copy_template(src: str, dst: str, module: str) -> None:
    src_path = Path(src)
    dst_resolved = dst.replace("{{module}}", module)
    dst_path = Path(dst_resolved)

    if not src_path.exists():
        print(f"   ⚠ Template not found: {src_path}")
        return

    dst_path.parent.mkdir(parents=True, exist_ok=True)

    if src_path.is_dir():
        if dst_path.exists():
            shutil.rmtree(dst_path)
        shutil.copytree(src_path, dst_path)
    else:
        shutil.copy2(src_path, dst_path)

    print(f"   ✓ {src} → {dst_resolved}")


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    """Run a command, return True on success."""
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except FileNotFoundError:
        print(f"   ⚠ Command not found: {cmd[0]}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"   ⚠ Failed: {' '.join(cmd)} (exit {e.returncode})")
        return False


def build_stack(args: argparse.Namespace) -> str:
    parts = ["Python · Claude Code · LangChain · Pydantic"]
    if args.with_vector_db:
        parts.append("Qdrant · Postgres")
    if args.with_frontend:
        parts.append("Next.js · FastAPI")
    return " · ".join(parts)


def build_architecture(args: argparse.Namespace) -> str:
    sections = []

    if args.with_vector_db:
        sections.append("""### The Ledger (Postgres)
Exact, structured data. Use for: counts, sums, averages, JOINs.

### The Memory (Qdrant)
Semantic data. Use for: meaning search, sentiment, free text.

### Routing rule
- Exact number → Ledger (SQL)
- Meaning / text → Memory (Qdrant)
- Hybrid → both""")

    if args.with_frontend:
        sections.append("""### Frontend
- FastAPI API: `src/{{project_name}}/api/` — runs on port 8000
- Next.js App: `frontend/` — runs on port 3000
- Communication: REST + SSE streaming via `/chat` endpoint
- Primitives: `frontend/components/primitives/`
- SSE client: `frontend/lib/sse.ts` — use `streamChat()` for streaming
- Stream hook: `frontend/hooks/useStream.ts` — use for any streaming feature""")

    if not sections:
        return "Single agent with Pydantic structured outputs and guardrails."
    return "\n\n".join(sections)


def build_extra_skills(args: argparse.Namespace) -> str:
    skills = []
    if args.with_vector_db:
        skills.append("- `qdrant` → vector store, embeddings, RAG pipeline")
        skills.append("- `postgres` → SQL patterns, canonical queries, SQLAlchemy")
    if args.with_frontend:
        skills.append("- `frontend` → Next.js, Tailwind, SSE streaming, FastAPI routes")
    return "\n".join(skills)


def build_commands(args: argparse.Namespace) -> str:
    cmds = []
    if args.with_vector_db:
        cmds.append("docker compose up -d                           # Start Postgres + Qdrant")
    if args.with_frontend:
        cmds.append("uv run uvicorn src.{{project_name}}.api.main:app --reload --port 8000  # FastAPI")
        cmds.append("cd frontend && npm run dev                     # Next.js on :3000")
        cmds.append("cd frontend && npm run test -- --run           # Frontend tests")
    cmds.append("uv run pytest --tb=short                        # Run unit tests")
    cmds.append("uv run pytest evals/ -m fast                    # Run fast behavioral evals")
    return "\n".join(cmds)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new project from agentic-starter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bootstrap.py --name "My Project" --author "Jane Doe"
  python bootstrap.py --name "My Project" --author "Jane Doe" --with-vector-db
  python bootstrap.py --name "My Project" --author "Jane Doe" --with-frontend
        """
    )
    parser.add_argument("--name", required=True, help='Project name')
    parser.add_argument("--author", required=True, help='Your name')
    parser.add_argument("--description",
                        default="AI project built with Claude Code",
                        help="Short one-line description")
    parser.add_argument("--with-vector-db", action="store_true",
                        help="Add Qdrant + Postgres + docker-compose")
    parser.add_argument("--with-frontend", action="store_true",
                        help="Add Next.js App Router + FastAPI backend API")
    parser.add_argument("--skip-git", action="store_true")
    args = parser.parse_args()

    project_slug = args.name.lower().replace(" ", "-")
    project_module = project_slug.replace("-", "_")

    print(f"\n🚀 Initializing: {args.name}")
    print(f"   author : {args.author}")
    print(f"   slug   : {project_slug}")
    if args.with_vector_db:
        print("   + vector-db (Qdrant + Postgres)")
    if args.with_frontend:
        print("   + frontend (Next.js + FastAPI)")
    print()

    # 1. Copy optional module files
    if args.with_vector_db:
        print("📂 Copying vector-db module...")
        for src, dst in VECTOR_DB_MANIFEST.items():
            copy_template(src, dst, project_module)

    if args.with_frontend:
        print("📂 Copying frontend module...")
        _frontend_module.apply(Path(".templates"), Path("."), project_module)

    # 2. Rename src/project_name
    old_src = Path("src/project_name")
    new_src = Path(f"src/{project_module}")
    if old_src.exists() and not new_src.exists():
        old_src.rename(new_src)
        print(f"\n📁 Renamed: src/project_name → src/{project_module}")

    # 3. Replace placeholders
    print("\n📝 Replacing placeholders...")
    replacements = {
        "{{project_name}}": project_slug,
        "{{PROJECT_NAME}}": args.name,
        "{{PROJECT_DESCRIPTION}}": args.description,
        "{{AUTHOR}}": args.author,
        "{{STACK}}": build_stack(args),
        "{{ARCHITECTURE_SECTION}}": build_architecture(args),
        "{{EXTRA_SKILLS}}": build_extra_skills(args),
        "{{EXTRA_AGENTS}}": "",
        "{{COMMANDS}}": build_commands(args),
        "project_name": project_module,
    }
    for path in Path(".").rglob("*"):
        if path.is_file() and path.suffix in TEXT_EXTENSIONS:
            if ".git" not in str(path) and ".templates" not in str(path):
                replace_in_file(path, replacements)
    # Also replace in frontend/ (excluded from the loop above to avoid .templates)
    if args.with_frontend and Path("frontend").exists():
        for path in Path("frontend").rglob("*"):
            if path.is_file() and path.suffix in TEXT_EXTENSIONS:
                replace_in_file(path, replacements)
    print("   ✓ Done")

    # 4. Create .env
    env_example = Path(".env.example")
    if env_example.exists() and not Path(".env").exists():
        Path(".env").write_text(env_example.read_text())
        print("\n🔑 .env created (fill in ANTHROPIC_API_KEY)")

    # 5. Create settings.local.json (vector-db only)
    if args.with_vector_db:
        example = Path(".claude/settings.local.json.example")
        local = Path(".claude/settings.local.json")
        if example.exists() and not local.exists():
            local.write_text(
                example.read_text().replace("project_name", project_module)
            )
            print("   ✓ .claude/settings.local.json created")

    # 6. Install Python dependencies + generate uv.lock
    print("\n🐍 Installing dependencies and generating uv.lock...")
    sync_cmd = ["uv", "sync", "--dev"]
    if args.with_vector_db:
        sync_cmd += ["--extra", "vector-db"]
    if args.with_frontend:
        sync_cmd += ["--extra", "frontend"]

    if run(sync_cmd):
        print("   ✓ Dependencies installed")
        print("   ✓ uv.lock generated (commit this file)")
    else:
        print("   → Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")

    # 7. Frontend post-install (npm install + .env.local)
    if args.with_frontend:
        _frontend_module.post_install(Path("."))

    # 8. Run base tests to confirm everything works
    print("\n🧪 Running base tests...")
    if run(["uv", "run", "pytest", "tests/", "--tb=short", "-q"]):
        print("   ✓ All base tests passing")
    else:
        print("   ⚠ Some tests failed — check output above")

    # 9. Initialize git
    if not args.skip_git and not Path(".git").exists():
        print("\n🔧 Initializing git...")
        run(["git", "init"])
        run(["git", "add", "."])
        run(["git", "commit", "-m", f"feat: initial setup — {args.name}"])
        print("   ✓ First commit created (includes uv.lock)")

    # 10. Next steps
    steps = ["1. Fill in .env with your ANTHROPIC_API_KEY"]
    n = 2
    if args.with_vector_db:
        steps.append(f"{n}. docker compose up -d")
        n += 1
    if args.with_frontend:
        steps.append(f"{n}. Set app.state.agent in src/{project_module}/api/main.py")
        n += 1
        steps.append(f"{n}. uv run uvicorn src.{project_module}.api.main:app --reload --port 8000")
        n += 1
        steps.append(f"{n}. cd frontend && npm run dev")
        n += 1
    steps.append(f"{n}. uv run pytest")
    n += 1
    steps.append(f"{n}. claude")
    n += 1
    steps.append(f"{n}. /brainstorm  ← start Phase 1")

    print(f"""
✅ {args.name} is ready!

Next steps:
{chr(10).join(f'  {s}' for s in steps)}

GitHub Actions CI is configured — add ANTHROPIC_API_KEY to repo secrets.
Docs: github.com/Juniordell/agentic-starter
""")


if __name__ == "__main__":
    main()
