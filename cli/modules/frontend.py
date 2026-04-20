"""Frontend module: Next.js App Router + FastAPI backend API."""

import logging
import shutil
import subprocess
from pathlib import Path

from cli.modules.base import Module

logger = logging.getLogger(__name__)


class FrontendModule(Module):
    name = "frontend"
    flag = "--with-frontend"
    description = "Next.js App Router + FastAPI backend API"
    extras = ["frontend"]

    def apply(self, templates_root: Path, dest: Path, module: str) -> None:
        """Copy Next.js app and FastAPI API module into the destination project."""
        # Copy Next.js app → frontend/
        src_nextjs = templates_root / "frontend" / "nextjs"
        dst_nextjs = dest / "frontend"
        if src_nextjs.exists():
            if dst_nextjs.exists():
                shutil.rmtree(dst_nextjs)
            shutil.copytree(src_nextjs, dst_nextjs)
            print(f"   ✓ Next.js app → {dst_nextjs}")
        else:
            logger.warning("Frontend template not found: %s", src_nextjs)

        # Copy FastAPI API module → src/{module}/api/
        src_api = templates_root / "frontend" / "api"
        dst_api = dest / "src" / module / "api"
        if src_api.exists():
            if dst_api.exists():
                shutil.rmtree(dst_api)
            shutil.copytree(src_api, dst_api)
            print(f"   ✓ FastAPI API → {dst_api}")
        else:
            logger.warning("API template not found: %s", src_api)

        # Copy test file → tests/test_api.py
        src_test = templates_root / "frontend" / "tests" / "test_api.py"
        dst_test = dest / "tests" / "test_api.py"
        if src_test.exists():
            shutil.copy2(src_test, dst_test)
            print(f"   ✓ tests/test_api.py")

    def post_install(self, dest: Path) -> None:
        """Create frontend/.env.local and run npm install."""
        frontend_dir = dest / "frontend"
        if not frontend_dir.exists():
            return

        # Create .env.local from example
        env_example = frontend_dir / ".env.local.example"
        env_local = frontend_dir / ".env.local"
        if env_example.exists() and not env_local.exists():
            env_local.write_text(env_example.read_text())
            print("   ✓ frontend/.env.local created")

        # Run npm install
        print("\n📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("   ✓ npm install complete")
        except FileNotFoundError:
            print("   ⚠ npm not found — run 'cd frontend && npm install' manually")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠ npm install failed (exit {e.returncode})")
