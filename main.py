import argparse
import os
import subprocess
import sys


def _dirs():
    """
    Resolve the absolute paths to the server and browser directories relative to this file.

    Inputs:
        None

    Outputs:
        server_dir  = absolute path to the server/ directory (str)
        browser_dir = absolute path to the browser/ directory (str)
    """
    root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, 'server'), os.path.join(root, 'browser')


def _open_browser_server(browser_dir, port):
    """
    Launch a Python HTTP server in a new terminal window to serve the browser UI files.
    The method used to open the terminal is platform-specific (cmd on Windows, Terminal.app
    on macOS, xterm on Linux).

    Inputs:
        browser_dir = absolute path to the directory to serve; passed as cwd to the HTTP server (str)
        port        = TCP port the HTTP server will listen on (int)

    Outputs:
        None. Side effect: a new terminal window opens running 'python -m http.server <port>'.
    """
    if sys.platform == 'win32':
        subprocess.Popen(
            f'start cmd /k python -m http.server {port}',
            shell=True,
            cwd=browser_dir
        )
    elif sys.platform == 'darwin':
        script = (
            f'tell app "Terminal" to do script '
            f'"cd {browser_dir} && python -m http.server {port}"'
        )
        subprocess.Popen(['osascript', '-e', script])
    else:
        subprocess.Popen(
            ['bash', '-c', f'xterm -e "python -m http.server {port}" &'],
            cwd=browser_dir
        )


def main():
    """
    Entry point for the Atlatl launcher. Parses command-line arguments, conditionally opens the
    browser HTTP server in a new terminal window when a human player is involved, prints the
    browser URL, and then runs server.py in the server/ directory as a blocking subprocess.

    Inputs (command-line arguments via sys.argv):
        scenario      = scenario .scn filename or built-in generator name, e.g. 'city-inf-5' (str, positional)
        --redAI       = AI agent name for the red side from server/airegistry.py; omit for a human player (str, optional)
        --blueAI      = AI agent name for the blue side from server/airegistry.py; omit for a human player (str, optional)
        --openSocket  = force the WebSocket to open even when both sides are AI-controlled (flag, optional)
        --port        = port for the browser HTTP server; default 8080 (int, optional)
        ...           = any additional arguments are forwarded unchanged to server.py

    Outputs:
        None. Side effects: starts server.py as a blocking subprocess; if a human is involved,
        also opens the browser HTTP server in a new terminal window and prints the browser URL
        to stdout.
    """
    parser = argparse.ArgumentParser(
        description='Atlatl launcher — runs a scenario and opens the browser server for human play.'
    )
    parser.add_argument('scenario', nargs='?', help='Scenario .scn file or generator name')
    parser.add_argument('--redAI',  help='AI name for red  (omit for a human player)')
    parser.add_argument('--blueAI', help='AI name for blue (omit for a human player)')
    parser.add_argument('--openSocket', action='store_true')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port for the browser HTTP server (default: 8080)')

    args, passthrough = parser.parse_known_args()

    if not args.scenario:
        parser.print_help()
        return

    server_dir, browser_dir = _dirs()

    human_blue = not args.blueAI
    human_red  = not args.redAI
    human_involved = human_blue or human_red or args.openSocket

    # Build the server.py command, forwarding all unrecognised args transparently
    server_cmd = [sys.executable, 'server.py', args.scenario]
    if args.redAI:
        server_cmd += ['--redAI',  args.redAI]
    if args.blueAI:
        server_cmd += ['--blueAI', args.blueAI]
    if human_involved:
        server_cmd.append('--openSocket')
    server_cmd += passthrough

    if human_involved:
        _open_browser_server(browser_dir, args.port)
        url = f'http://localhost:{args.port}/play.html'
        print()
        print(f'  Browser UI: {url}')
        if human_blue and human_red:
            print('  Open the URL in two browser tabs.')
            print('  Select Blue in one tab and Red in the other.')
        elif human_blue:
            print('  Open the URL in a browser and select Blue.')
        else:
            print('  Open the URL in a browser and select Red.')
        print()

    subprocess.run(server_cmd, cwd=server_dir)


if __name__ == '__main__':
    main()
