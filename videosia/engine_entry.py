"""Defensa de privacidad para sockets Python antes de importar el motor.

No es un sandbox contra código malicioso: un ejecutable nativo o subprocess
puede evitar este hook. Docker --network none proporciona el límite de red.
"""

import runpy
import sys
from pathlib import Path

BLOCKED_NETWORK_EVENTS = frozenset({
    "socket.connect", "socket.bind", "socket.getaddrinfo", "socket.sendto", "socket.sendmsg",
    "socket.gethostbyname", "socket.gethostbyaddr", "socket.getnameinfo",
})
BLOCK_MESSAGE = "VideosIA bloqueó una operación de red de Python en el perfil local"


def block_network(event, _arguments):
    if event in BLOCKED_NETWORK_EVENTS:
        # Never put destination hosts, addresses, prompts or credentials in this error.
        raise PermissionError(BLOCK_MESSAGE)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Falta el punto de entrada del motor")
    entrypoint = Path(sys.argv[1]).resolve(strict=True)
    sys.addaudithook(block_network)
    sys.path.insert(0, str(entrypoint.parent))
    sys.argv = [str(entrypoint), *sys.argv[2:]]
    runpy.run_path(str(entrypoint), run_name="__main__")


if __name__ == "__main__":
    main()
