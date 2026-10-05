"""S08 real server bootstrap and bounded ownership of child interpreters.

The serve wrapper only reports the OS-assigned port after the real bind. Game,
transport, routing, exit, and replay code run unchanged in the child.
"""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

from tests.support.builders import load_fixture
from tests.support.imports import REPO_ROOT, SERVER_DIR, TESTS_DIR


def child_env(cwd):
    env = {key: value for key, value in os.environ.items()
           if not any(part in key.upper() for part in ("MODEL", "CHECKPOINT", "NEURAL"))}
    env.update(ATLATL_NEURAL="0", PYTHONHASHSEED="1729", PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=os.pathsep.join((str(REPO_ROOT), str(SERVER_DIR))))
    env.update({key: str(cwd) for key in ("TMP", "TEMP", "TMPDIR")})
    return env


class Child:
    def __init__(self, args, cwd, name):
        self.cwd = Path(cwd).resolve()
        assert self.cwd.is_relative_to(TESTS_DIR / ".tmp")
        self.stdout_path = self.cwd / f"{name}.stdout"
        self.stderr_path = self.cwd / f"{name}.stderr"
        self.stdout = self.stdout_path.open("w", encoding="utf-8")
        self.stderr = self.stderr_path.open("w", encoding="utf-8")
        try:
            self.process = subprocess.Popen(
                [str(Path(sys.executable).resolve()), "-B", "-u", *args],
                cwd=self.cwd, env=child_env(self.cwd),
                stdout=self.stdout, stderr=self.stderr)
        except BaseException:
            self.stdout.close()
            self.stderr.close()
            raise

    def diagnostics(self):
        return (f"stdout:\n{self.stdout_path.read_text(encoding='utf-8')}\n"
                f"stderr:\n{self.stderr_path.read_text(encoding='utf-8')}")

    def wait(self, timeout=30, expected=0):
        try:
            code = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise AssertionError(f"Child deadline exceeded\n{self.diagnostics()}") from exc
        if expected is not None:
            assert code == expected, self.diagnostics()
        return code

    def ready(self, filename="ready.json", timeout=15):
        deadline = time.monotonic() + timeout
        path = self.cwd / filename
        while time.monotonic() < deadline:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            assert self.process.poll() is None, self.diagnostics()
            time.sleep(0.01)
        raise AssertionError(f"No bound-server readiness\n{self.diagnostics()}")

    def close(self):
        try:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        finally:
            self.stdout.close()
            self.stderr.close()
        assert self.process.poll() is not None


@contextmanager
def owned_child(args, cwd, name="child"):
    child = Child(args, cwd, name)
    try:
        yield child
    finally:
        child.close()


@contextmanager
def running_server(cwd, **config):
    path = Path(cwd) / "server-config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with owned_child(["-m", "tests.support.integration_server", str(path)], cwd, "server") as child:
        yield child


def read_report(cwd):
    report = json.loads((Path(cwd) / "report.json").read_text(encoding="utf-8"))
    assert not report["timeout"]
    assert not report["task_errors"]
    assert report["pending_tasks"] == 0
    assert report["loop_closed"] and report["logs_closed"]
    if report["reps_done"]:
        assert report["production_logs_closed"]
    return report


def run_server(config):
    import websockets
    from game_dispenser import ScenarioGeneratorGameDispenser
    from gameserver import GameServer

    random.seed(1729)
    episode = load_fixture("scenarios/tiny_episode.json")
    scenario = config.get("scenario", episode["scenario"])
    actions = config.get("actions", episode["actions"])
    transcripts = {role: [] for role in config.get("functions", [])}

    def client(role):
        def process(wire, response_fn=None):
            msg = json.loads(wire)
            transcripts[role].append(msg)
            if msg["type"] == "parameters":
                return json.dumps({"type": "role-request", "role": role})
            obs = msg["observation"]
            if not obs["status"]["isTerminal"] and obs["status"]["onMove"] == role:
                return json.dumps({"type": "action", "action": actions[obs["status"]["phaseCount"]]})
            return None
        return process

    real_serve = websockets.serve
    bound_servers = []

    @asynccontextmanager
    async def reporting_serve(*args, **kwargs):
        async with real_serve(*args, **kwargs) as server:
            bound_servers.append(server)
            ready = Path("ready.pending")
            ready.write_text(json.dumps({"port": server.sockets[0].getsockname()[1]}), encoding="utf-8")
            ready.replace("ready.json")
            yield server

    websockets.serve = reporting_serve
    previous_signal = signal.getsignal(signal.SIGINT)
    gs = GameServer(ScenarioGeneratorGameDispenser(lambda: deepcopy(scenario)),
                    [client(role) for role in transcripts], port=0,
                    open_socket=config.get("socket", False), n_reps=config.get("reps", 1),
                    blue_log="blue.js", red_log="red.js", log_actions=config.get("log_actions", False))
    loop = gs.message_server.loop
    # Own startup tasks until teardown. asyncio keeps weak task references;
    # the socket task awaits a private Future before a client connects, so a
    # larger scenario's allocations can otherwise collect that pending task.
    startup_tasks = tuple(asyncio.all_tasks(loop))
    task_errors = []

    def record_task_error(loop, context):
        task_errors.append(str(context.get("exception", context["message"])))

    loop.set_exception_handler(record_task_error)
    timed_out = False

    def deadline():
        nonlocal timed_out
        timed_out = True
        loop.stop()

    watchdog = loop.call_later(25, deadline)
    try:
        gs.run()
    finally:
        watchdog.cancel()
        production_logs_closed = gs.blue_logfile.closed and gs.red_logfile.closed
        # Cancel application handlers (including do_exit) first. Keep the
        # WebSocket library's close/keepalive tasks alive through its shutdown.
        application_tasks = [task for task in asyncio.all_tasks(loop)
                             if task.get_coro().__name__ in ("process_function_client", "conn_handler")]
        for task in application_tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*application_tasks, return_exceptions=True))
        connections = [wrapper.client for wrapper in gs.message_server.clients
                       if wrapper.type == "websocket"]
        loop.run_until_complete(asyncio.wait_for(
            asyncio.gather(*(connection.close() for connection in connections)), timeout=5))
        for server in bound_servers:
            server.close()
            loop.run_until_complete(asyncio.wait_for(server.wait_closed(), timeout=5))
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        assert all(task.done() for task in startup_tasks)
        for logfile in (gs.blue_logfile, gs.red_logfile):
            if not logfile.closed:
                logfile.write("]\n")
                logfile.close()
        report = dict(state=gs.game_state, reps_done=gs.reps_done,
                      transcripts=transcripts, clients=len(gs.message_server.clients),
                      roles=gs.clientIdToRole, timeout=timed_out, task_errors=task_errors,
                      pending_tasks=len(asyncio.all_tasks(loop)),
                      production_logs_closed=production_logs_closed,
                      logs_closed=gs.blue_logfile.closed and gs.red_logfile.closed)
        loop.close()
        report["loop_closed"] = loop.is_closed()
        asyncio.set_event_loop(None)
        signal.signal(signal.SIGINT, previous_signal)
        websockets.serve = real_serve
        Path("report.json").write_text(json.dumps(report), encoding="utf-8")


if __name__ == "__main__":
    run_server(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
