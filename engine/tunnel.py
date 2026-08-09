"""Give the shared world a public address, for people not on your wifi.

Your phone has no address the wider internet can dial. A tunnel program makes
an outbound connection to a company's server and lends you one of their
addresses, forwarding anything that arrives back down to Spark.

Spark does not ship one and cannot install one. It looks for a tunnel you have
already installed, runs it, and reads the address out of its output.

    cloudflared   pkg install cloudflared   no account needed for a quick link
    ngrok         pkg install ngrok         needs a free account and a token
"""

import re
import shutil
import subprocess
import threading
import time

# How to run each one, and how to recognise the address it prints.
TUNNELS = [
    ("cloudflared",
     lambda port: ["cloudflared", "tunnel", "--url", "http://127.0.0.1:%d" % port],
     re.compile(r"https://[\w-]+\.trycloudflare\.com")),
    ("ngrok",
     lambda port: ["ngrok", "http", str(port), "--log", "stdout"],
     re.compile(r"https://[\w-]+\.ngrok[\w.-]*\.\w+")),
]


def available():
    return [name for name, _, _ in TUNNELS if shutil.which(name)]


def advice():
    return ("No tunnel program found. Install one first:\n"
            "    pkg install cloudflared     (no account needed)\n"
            "    pkg install ngrok           (free account, then `ngrok config`)\n"
            "Without one, others can still join over your wifi.")


class Tunnel:
    """A running tunnel, and the address it handed us."""

    def __init__(self, port):
        self.port = port
        self.process = None
        self.url = None
        self.name = None

    def start(self, timeout=25):
        for name, command, pattern in TUNNELS:
            if not shutil.which(name):
                continue
            self.name = name
            self.process = subprocess.Popen(
                command(self.port), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1)
            threading.Thread(target=self._read, args=(pattern,),
                             daemon=True).start()
            deadline = time.time() + timeout
            while time.time() < deadline and self.url is None:
                if self.process.poll() is not None:
                    break
                time.sleep(0.3)
            if self.url:
                return self.url
            self.stop()
        return None

    def _read(self, pattern):
        for line in self.process.stdout:
            found = pattern.search(line)
            if found and self.url is None:
                self.url = found.group(0)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
