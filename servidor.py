"""
Simulação do Algoritmo Bully para Eleição de Líder
Sistemas Distribuídos - Protótipo Python
"""

import threading
import time
import random
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

# ─────────────────────────────────────────────────────────────
# Modelo de Processo
# ─────────────────────────────────────────────────────────────

class Process:
    def __init__(self, pid: int):
        self.pid = pid
        self.alive = True
        self.is_leader = False
        self.in_election = False
        self.waiting_ok = False   # aguardando OK de processo com ID maior

    def to_dict(self):
        return {
            "pid": self.pid,
            "alive": self.alive,
            "is_leader": self.is_leader,
            "in_election": self.in_election,
        }


# ─────────────────────────────────────────────────────────────
# Simulador Bully
# ─────────────────────────────────────────────────────────────

class BullySimulator:
    def __init__(self, num_processes: int = 5):
        self.lock = threading.Lock()
        self.messages: list[dict] = []
        self.processes: list[Process] = []
        self.leader_pid: int | None = None
        self.running = False
        self.reset(num_processes)

    # ── helpers ──────────────────────────────────────────────

    def reset(self, num_processes: int = 5):
        with self.lock:
            self.processes = [Process(i + 1) for i in range(num_processes)]
            self.messages = []
            self.leader_pid = None
            self.running = False
            # elege o de maior PID como líder inicial
            self._elect_initial_leader()

    def _elect_initial_leader(self):
        alive = [p for p in self.processes if p.alive]
        if alive:
            leader = max(alive, key=lambda p: p.pid)
            leader.is_leader = True
            self.leader_pid = leader.pid
            self._log("SISTEMA", "INIT",
                       f"Líder inicial: Processo {leader.pid}",
                       highlight=True)

    def _log(self, sender: str, msg_type: str, detail: str,
             receiver: str = "TODOS", highlight: bool = False):
        entry = {
            "id": len(self.messages),
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "sender": str(sender),
            "receiver": str(receiver),
            "type": msg_type,
            "detail": detail,
            "highlight": highlight,
        }
        self.messages.append(entry)

    def _get_alive(self):
        return [p for p in self.processes if p.alive]

    def _process(self, pid: int) -> Process | None:
        for p in self.processes:
            if p.pid == pid:
                return p
        return None

    # ── API actions ──────────────────────────────────────────

    def kill_leader(self):
        """Mata o líder atual e dispara nova eleição."""
        with self.lock:
            if self.leader_pid is None:
                return {"ok": False, "msg": "Sem líder atual."}
            leader = self._process(self.leader_pid)
            if leader is None or not leader.alive:
                return {"ok": False, "msg": "Líder já está morto."}

            leader.alive = False
            leader.is_leader = False
            old = self.leader_pid
            self.leader_pid = None
            self._log("SISTEMA", "FALHA",
                      f"Processo {old} (líder) falhou!", highlight=True)

        # dispara eleição em thread separada
        threading.Thread(target=self._run_election, daemon=True).start()
        return {"ok": True, "msg": f"Processo {old} removido. Eleição iniciada."}

    def kill_process(self, pid: int):
        """Mata um processo arbitrário."""
        with self.lock:
            p = self._process(pid)
            if p is None:
                return {"ok": False, "msg": "Processo não encontrado."}
            if not p.alive:
                return {"ok": False, "msg": f"Processo {pid} já está morto."}
            p.alive = False
            was_leader = p.is_leader
            p.is_leader = False
            if was_leader:
                self.leader_pid = None
                self._log("SISTEMA", "FALHA",
                          f"Processo {pid} (líder) falhou!", highlight=True)
            else:
                self._log("SISTEMA", "FALHA",
                          f"Processo {pid} falhou.")

        if was_leader:
            threading.Thread(target=self._run_election, daemon=True).start()
        return {"ok": True, "msg": f"Processo {pid} removido." +
                (" Eleição iniciada." if was_leader else "")}

    def revive_process(self, pid: int):
        """Revive um processo morto."""
        with self.lock:
            p = self._process(pid)
            if p is None:
                return {"ok": False, "msg": "Processo não encontrado."}
            if p.alive:
                return {"ok": False, "msg": f"Processo {pid} já está vivo."}
            p.alive = True
            self._log("SISTEMA", "RECUPERAÇÃO",
                      f"Processo {pid} voltou à rede.", highlight=True)

        # se o processo reativado tem PID maior que o líder atual, ele
        # pode iniciar uma nova eleição (comportamento Bully)
        def maybe_elect():
            time.sleep(0.4)
            with self.lock:
                if self.leader_pid is not None and pid > self.leader_pid:
                    self._log(f"P{pid}", "ELEIÇÃO",
                              f"Processo {pid} retornou com PID maior que líder {self.leader_pid}. Iniciando eleição.")
            self._run_election(initiator=pid)

        threading.Thread(target=maybe_elect, daemon=True).start()
        return {"ok": True, "msg": f"Processo {pid} reativado."}

    def start_election(self, initiator_pid: int | None = None):
        """Dispara eleição manualmente."""
        with self.lock:
            alive = self._get_alive()
            if not alive:
                return {"ok": False, "msg": "Nenhum processo vivo."}
            if initiator_pid is None:
                initiator_pid = random.choice(alive).pid
        threading.Thread(target=self._run_election,
                         kwargs={"initiator": initiator_pid},
                         daemon=True).start()
        return {"ok": True, "msg": f"Eleição iniciada pelo Processo {initiator_pid}."}

    def add_process(self):
        """Adiciona um novo processo com PID máximo+1."""
        with self.lock:
            new_pid = max(p.pid for p in self.processes) + 1
            self.processes.append(Process(new_pid))
            self._log("SISTEMA", "NOVO",
                      f"Processo {new_pid} adicionado à rede.", highlight=True)
        return {"ok": True, "msg": f"Processo {new_pid} adicionado."}

    # ── Bully Algorithm ──────────────────────────────────────

    def _run_election(self, initiator: int | None = None):
        """Executa o algoritmo Bully de forma simulada e sequencial."""
        time.sleep(0.3)  # pequeno delay para parecer assíncrono

        with self.lock:
            alive = self._get_alive()
            if not alive:
                self._log("SISTEMA", "ERRO", "Nenhum processo vivo para eleger líder.")
                return

            if initiator is None:
                initiator = min(alive, key=lambda p: p.pid).pid

            self._log(f"P{initiator}", "ELEIÇÃO",
                      f"Processo {initiator} detectou ausência de líder e inicia eleição.",
                      highlight=True)

            # marca todos em eleição
            for p in alive:
                p.in_election = True

        time.sleep(0.5)

        # fase 1: cada processo envia ELECTION para processos com PID maior
        with self.lock:
            alive_pids = sorted([p.pid for p in self._get_alive()])

        responses: dict[int, bool] = {}   # pid -> recebeu OK?

        for pid in alive_pids:
            higher = [h for h in alive_pids if h > pid]
            if higher:
                msg = f"Processo {pid} envia ELECTION para {higher}"
                with self.lock:
                    self._log(f"P{pid}", "ELECTION",
                              msg,
                              receiver=", ".join(f"P{h}" for h in higher))
                time.sleep(0.3)

                # processos com PID maior respondem OK
                with self.lock:
                    ok_from = []
                    for h in higher:
                        ph = self._process(h)
                        if ph and ph.alive:
                            ok_from.append(h)
                            self._log(f"P{h}", "OK",
                                      f"Processo {h} responde OK para Processo {pid}",
                                      receiver=f"P{pid}")
                    responses[pid] = len(ok_from) > 0
                time.sleep(0.2)

        time.sleep(0.4)

        # fase 2: quem não recebeu OK se declara coordenador
        with self.lock:
            alive_pids = sorted([p.pid for p in self._get_alive()])
            winner = max(alive_pids)

            # limpa estado de eleição
            for p in self.processes:
                p.in_election = False
                p.is_leader = False

            new_leader = self._process(winner)
            if new_leader:
                new_leader.is_leader = True
                self.leader_pid = winner
                self._log(f"P{winner}", "COORDINATOR",
                          f"Processo {winner} se declara COORDENADOR e notifica todos.",
                          receiver="TODOS", highlight=True)

            # notifica todos
            for pid in alive_pids:
                if pid != winner:
                    self._log(f"P{winner}", "COORDINATOR",
                              f"Processo {pid} reconhece Processo {winner} como novo líder.",
                              receiver=f"P{pid}")

            self._log("SISTEMA", "FIM",
                      f"✓ Eleição concluída. Novo líder: Processo {winner}.",
                      highlight=True)

    # ── State snapshot ────────────────────────────────────────

    def state(self):
        with self.lock:
            return {
                "processes": [p.to_dict() for p in self.processes],
                "leader_pid": self.leader_pid,
                "messages": list(self.messages),
            }


# ─────────────────────────────────────────────────────────────
# HTTP Server
# ─────────────────────────────────────────────────────────────

simulator = BullySimulator(num_processes=5)


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silencia logs de requisição

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/state":
            self._json(simulator.state())
        elif path == "/reset":
            qs = parse_qs(parsed.query)
            n = int(qs.get("n", ["5"])[0])
            simulator.reset(n)
            self._json({"ok": True})
        elif path == "/kill_leader":
            self._json(simulator.kill_leader())
        elif path == "/start_election":
            qs = parse_qs(parsed.query)
            pid = qs.get("pid", [None])[0]
            self._json(simulator.start_election(int(pid) if pid else None))
        elif path == "/kill":
            qs = parse_qs(parsed.query)
            pid = int(qs.get("pid", ["1"])[0])
            self._json(simulator.kill_process(pid))
        elif path == "/revive":
            qs = parse_qs(parsed.query)
            pid = int(qs.get("pid", ["1"])[0])
            self._json(simulator.revive_process(pid))
        elif path == "/add":
            self._json(simulator.add_process())
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()


def run_server(port: int = 8765):
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[Bully Server] rodando em http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
