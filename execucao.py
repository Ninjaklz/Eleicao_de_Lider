#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   ELEIÇÃO DE LÍDER — ALGORITMO BULLY                        ║
║   Simulação de Sistemas Distribuídos — 2026-1               ║
╚══════════════════════════════════════════════════════════════╝

COMO EXECUTAR:
  python3 execucao.py

  O script sobe dois servidores:
    • API  (lógica Bully)  → http://localhost:8765
    • HTML (frontend)      → http://localhost:8080

  O navegador abrirá automaticamente em http://localhost:8080/frontend_servidor.html
  Pressione Ctrl+C para encerrar tudo.
"""

import subprocess
import sys
import os
import webbrowser
import time

# ── Nomes dos arquivos ────────────────────────────────────────
SERVER_FILE   = "servidor.py"
FRONTEND_FILE = "frontend_servidor.html"
API_PORT      = 8765
FRONTEND_PORT = 8080

def main():
    print(__doc__)

    # Diretório base = onde este script está salvo
    base_dir = os.path.dirname(os.path.abspath(__file__))

    server_path   = os.path.join(base_dir, SERVER_FILE)
    frontend_path = os.path.join(base_dir, FRONTEND_FILE)

    # ── Verificações ──────────────────────────────────────────
    if not os.path.exists(server_path):
        print(f"ERRO: '{SERVER_FILE}' não encontrado em {base_dir}")
        sys.exit(1)
    if not os.path.exists(frontend_path):
        print(f"ERRO: '{FRONTEND_FILE}' não encontrado em {base_dir}")
        sys.exit(1)

    # ── 1. Sobe o servidor da API Bully ──────────────────────
    print(f"► Iniciando API Bully em http://localhost:{API_PORT} ...")
    proc_api = subprocess.Popen(
        [sys.executable, SERVER_FILE],
        cwd=base_dir,                  # garante execução no diretório correto
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # ── 2. Sobe o servidor HTTP para o frontend ───────────────
    # Usar http.server evita bloqueios CORS do protocolo file://
    print(f"► Iniciando servidor HTTP do frontend em http://localhost:{FRONTEND_PORT} ...")
    proc_http = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(FRONTEND_PORT)],
        cwd=base_dir,                  # serve os arquivos desta pasta
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1.5)   # aguarda os dois processos ficarem prontos

    url = f"http://localhost:{FRONTEND_PORT}/{FRONTEND_FILE}"
    print(f"► Abrindo navegador em: {url}")
    webbrowser.open(url)

    print("\n✓ Simulação rodando!")
    print(f"  API      → http://localhost:{API_PORT}")
    print(f"  Frontend → {url}")
    print("  Pressione Ctrl+C para encerrar.\n")

    try:
        proc_api.wait()
    except KeyboardInterrupt:
        print("\n[Encerrando servidores...]")
        proc_api.terminate()
        proc_http.terminate()
        print("[Encerrado]")

if __name__ == "__main__":
    main()
