# Eleição de Líder — Algoritmo Bully
### Simulação de Sistemas Distribuídos · 2026-1

---

## Estrutura dos Arquivos

```
bully_server.py      ← Backend Python (lógica do algoritmo + servidor HTTP)
bully_frontend.html  ← Interface visual interativa (abrir no navegador)
executar.py          ← Script de inicialização automática
README.md            ← Este arquivo
```

---

## Como executar

### Opção 1 — Script automático (recomendado)
```bash
python3 executar.py
```
Isso inicia o servidor e abre o frontend automaticamente.

### Opção 2 — Manual
```bash
# Terminal 1: servidor
python3 bully_server.py

# Depois abra bully_frontend.html no navegador
```

**Requisitos:** Python 3.9+ (apenas bibliotecas padrão, sem instalação extra)

---

## O que a simulação demonstra

### Algoritmo Bully

O **Algoritmo Bully** é um clássico protocolo de eleição de líder em sistemas distribuídos. Ele funciona assim:

1. **Detecção de falha**: Um processo percebe que o líder atual não responde.
2. **Envio de ELECTION**: O processo envia mensagem `ELECTION` a todos com PID maior.
3. **Resposta OK**: Processos com PID maior respondem `OK`, assumindo controle da eleição.
4. **Declaração COORDINATOR**: O processo com maior PID vivo se declara líder e envia `COORDINATOR` a todos.

### Por que "Bully"?
O maior processo "intimida" (bully) os menores e assume o comando.

---

## Funcionalidades Interativas

| Botão / Ação | O que faz |
|---|---|
| 💀 **Matar Líder** | Remove o líder atual e dispara eleição automática |
| ⚡ **Iniciar Eleição** | Força início de eleição por processo aleatório |
| ➕ **Novo Processo** | Adiciona processo com PID maior (aciona nova eleição) |
| 🔄 **Reiniciar** | Reseta a simulação (3 a 7 processos) |
| Clique no card | Abre menu: Matar / Reviver / Iniciar eleição daquele processo |

---

## Mensagens trocadas (Log)

| Tipo | Significado |
|---|---|
| `INIT` | Configuração inicial do sistema |
| `FALHA` | Processo falhou (saiu da rede) |
| `ELEIÇÃO` | Processo detectou ausência de líder e inicia eleição |
| `ELECTION` | Mensagem enviada a processos com PID maior |
| `OK` | Resposta de processo com PID maior |
| `COORDINATOR` | Declaração do novo líder |
| `FIM` | Eleição concluída |
| `RECUPERAÇÃO` | Processo voltou à rede |

---

## Conceitos Teóricos

- **PID (Process ID)**: Identificador único de cada processo
- **Líder/Coordenador**: Processo responsável pela coordenação distribuída
- **Falha de processo**: Simulada matando um nó
- **Eleição**: Mecanismo para escolher novo coordenador após falha
- **Mensagem ELECTION**: Enviada para processos superiores
- **Mensagem OK**: Confirma que processo superior assumirá a eleição
- **Mensagem COORDINATOR**: Anuncia o vencedor da eleição

---

## Referências

- Tanenbaum, A. S. & Van Steen, M. — *Distributed Systems: Principles and Paradigms*
- Garcia-Molina, H. (1982) — *Elections in a Distributed Computing System* (IEEE)
- Coulouris, G. et al. — *Distributed Systems: Concepts and Design*
