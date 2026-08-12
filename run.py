#!/usr/bin/env python3
"""Start or reuse the local Claude container and launch an interactive session."""

from __future__ import annotations

import argparse
import os
import pwd
import grp
import re
import shutil
import subprocess
import sys
from pathlib import Path



PROJECT_DIR = Path(__file__).resolve().parent
COMPOSE_FILE = PROJECT_DIR / "docker-compose.yml"
ENV_FILE = PROJECT_DIR / ".env"
ENV_EXAMPLE_FILE = PROJECT_DIR / ".env.example"


def parse_args() -> argparse.Namespace:
	"""Parse command line arguments for interactive session mode."""
	parser = argparse.ArgumentParser(
		description="Start or reuse the local Claude container and open a shell session."
	)
	parser.add_argument(
		"--root",
		action="store_true",
		help="Open an interactive root shell instead of launching claude.",
	)
	return parser.parse_args()


def ensure_env_file_exists() -> None:
	"""Ensure .env exists, creating it from .env.example on first run."""
	if ENV_FILE.exists():
		return

	if not ENV_EXAMPLE_FILE.exists():
		fail(f"Missing {ENV_FILE} and template {ENV_EXAMPLE_FILE}.")

	try:
		shutil.copy2(ENV_EXAMPLE_FILE, ENV_FILE)
		ENV_EXAMPLE_FILE.unlink()
	except OSError as error:
		fail(f"Could not initialize {ENV_FILE.name} from {ENV_EXAMPLE_FILE.name}: {error}")

def _owner_mode(path: Path) -> str:
	stat = path.stat()
	try:
		owner = pwd.getpwuid(stat.st_uid).pw_name
	except KeyError:
		owner = str(stat.st_uid)
	try:
		group = grp.getgrgid(stat.st_gid).gr_name
	except KeyError:
		group = str(stat.st_gid)
	mode = oct(stat.st_mode & 0o777)
	return f"{owner}:{group} {mode}"


def fail(message: str, code: int = 1) -> None:
	print(f"❌ {message}")
	sys.exit(code)


def run(cmd: list[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
	return subprocess.run(
		cmd,
		cwd=PROJECT_DIR,
		check=check,
		text=True,
		capture_output=capture,
	)


def get_service_name() -> str:
	result = run(["docker", "compose", "config", "--services"], check=False, capture=True)
	if result.returncode != 0:
		fail("Could not resolve service name from docker-compose.yml.")

	services = [line.strip() for line in result.stdout.splitlines() if line.strip()]
	if not services:
		fail("No services found in docker-compose.yml.")

	return services[0]


def is_container_running() -> bool:
	service_name = get_service_name()
	container_id = run(["docker", "compose", "ps", "-q", service_name], check=False, capture=True)
	if container_id.returncode != 0 or not container_id.stdout.strip():
		return False

	container_ref = container_id.stdout.strip().splitlines()[0]
	result = run(
		["docker", "inspect", "-f", "{{.State.Running}}", container_ref],
		check=False,
		capture=True,
	)
	if result.returncode != 0:
		return False
	return result.stdout.strip().lower() == "true"


def ensure_runtime_prereqs() -> None:
	if shutil.which("docker") is None:
		fail("Docker is not installed or not available in PATH.")

	compose_ok = subprocess.run(
		["docker", "compose", "version"],
		cwd=PROJECT_DIR,
		check=False,
		text=True,
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL,
	).returncode == 0

	if not compose_ok:
		fail("Docker Compose plugin is not available. Install Docker Compose v2.")


def ensure_writable_directory(path: Path, label: str) -> None:
	try:
		path.mkdir(parents=True, exist_ok=True)
	except PermissionError:
		fail(f"Cannot create {label} at {path}. Check directory ownership/permissions.")

	if not os.access(path, os.R_OK | os.W_OK | os.X_OK):
		fail(
			f"{label} is not writable by current user ({path}, owner {_owner_mode(path)}). "
			"Fix permissions before starting the container."
		)


def _load_dotenv() -> dict[str, str]:
	env_data: dict[str, str] = {}
	ensure_env_file_exists()
	if not ENV_FILE.exists():
		return env_data

	for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		name, value = line.split("=", 1)
		env_data[name.strip()] = value.strip().strip('"').strip("'")
	return env_data


def _expand_compose_var(text: str, env_data: dict[str, str]) -> str:
	"""Expand ${VAR} and ${VAR:-default} syntax used in docker-compose files."""

	def replace(match: re.Match[str]) -> str:
		var_name = match.group(1)
		default_value = match.group(2)
		if var_name in os.environ and os.environ[var_name] != "":
			return os.environ[var_name]
		if var_name in env_data and env_data[var_name] != "":
			return env_data[var_name]
		return default_value or ""

	pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
	return pattern.sub(replace, text)


def _get_container_home(env_data: dict[str, str]) -> str:
	"""Resolve container HOME path from docker-compose.yml environment section."""
	for raw_line in COMPOSE_FILE.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line.startswith("- HOME="):
			continue
		home_value = line[len("- HOME=") :].strip()
		home_value = _expand_compose_var(home_value, env_data)
		if home_value:
			return home_value

	return "/home/claude"


def _parse_compose_mounts() -> dict[str, Path]:
	"""Return host paths for key container mount targets from docker-compose.yml."""
	if not COMPOSE_FILE.exists():
		fail(f"Missing compose file: {COMPOSE_FILE}")
	env_data = _load_dotenv()
	container_home = _get_container_home(env_data)

	mount_targets = {
		container_home: "Claude home mount",
	}

	found: dict[str, Path] = {}
	for raw_line in COMPOSE_FILE.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line.startswith("- "):
			continue

		entry = line[2:].split(" #", 1)[0].strip()
		if ":" not in entry:
			continue

		parts = entry.split(":")
		if len(parts) < 2:
			continue

		host_raw = _expand_compose_var(parts[0].strip(), env_data)
		target = _expand_compose_var(parts[1].strip(), env_data)
		if target not in mount_targets:
			continue

		# Only validate bind mounts with filesystem paths.
		if not (host_raw.startswith("/") or host_raw.startswith("~") or host_raw.startswith(".")):
			continue

		host_path = Path(host_raw).expanduser()
		if host_raw.startswith("."):
			host_path = (PROJECT_DIR / host_raw).resolve()

		found[mount_targets[target]] = host_path

	return found


def preflight_checks() -> None:
	compose_check = subprocess.run(
		["docker", "compose", "config"],
		cwd=PROJECT_DIR,
		check=False,
		text=True,
		stdout=subprocess.DEVNULL,
		stderr=subprocess.PIPE,
	)
	if compose_check.returncode != 0:
		error = compose_check.stderr.strip() or "Unknown docker compose configuration error."
		fail(f"docker-compose.yml validation failed: {error}")

	mounts = _parse_compose_mounts()
	if not mounts:
		fail("Could not detect Claude bind mounts in docker-compose.yml volumes.")

	for label, host_path in mounts.items():
		ensure_writable_directory(host_path, label)


def ensure_container_running() -> None:
	if is_container_running():
		return

	service_name = get_service_name()
	mounts = _parse_compose_mounts()
	print("🔍 Container not detected. Starting secure environment...")

	# Keep host UID/GID in sync with the build args when not explicitly set.
	env = os.environ.copy()
	env.setdefault("LOCAL_UID", str(os.getuid()))
	home_mount = mounts.get("Claude home mount")
	default_gid = str(home_mount.stat().st_gid) if home_mount is not None else str(os.getgid())
	env.setdefault("LOCAL_GID", default_gid)

	# Fast path: start without forcing a rebuild every time.
	up_cmd = ["docker", "compose", "up", "-d", service_name]
	start = subprocess.run(up_cmd, cwd=PROJECT_DIR, env=env, check=False, text=True)
	if start.returncode != 0:
		print("⚠️  Start without rebuild failed. Retrying with image build...")
		build_cmd = ["docker", "compose", "up", "-d", "--build", service_name]
		start = subprocess.run(build_cmd, cwd=PROJECT_DIR, env=env, check=False, text=True)
		if start.returncode != 0:
			fail("Failed to start container with docker compose up -d.")

	if not is_container_running():
		fail("Container did not reach running state after startup.")

	print("✅ Environment ready. Starting Claude Code session...")


def launch_interactive_session(*, root_mode: bool = False) -> None:
	service_name = get_service_name()
	# Replace the Python process with docker compose exec for a clean terminal handoff.
	if root_mode:
		exec_cmd = [
			"docker",
			"compose",
			"exec",
			"--user",
			"root",
			service_name,
			"bash",
		]
	else:
		exec_cmd = [
			"docker",
			"compose",
			"exec",
			service_name,
			"claude",
		]
	os.chdir(PROJECT_DIR)
	try:
		os.execvp(exec_cmd[0], exec_cmd)
	except OSError as error:
		fail(f"Could not open Claude Code session: {error}")


def main() -> None:
	args = parse_args()
	ensure_runtime_prereqs()
	preflight_checks()
	ensure_container_running()
	launch_interactive_session(root_mode=args.root)


if __name__ == "__main__":
	main()

# x