#!/usr/bin/env python3
"""
gu_alert.py — Monitor de tokens novos na GU Factory (gu.exchange)

O que faz:
  - Consulta https://api.gu.exchange/metrics/volume de tempos em tempos
  - Sempre que aparece um token que ainda não tinha sido visto, mostra na hora
  - Mostra a rede (chain) onde o token foi criado
  - Se nome, símbolo OU a moeda de reserva bater com uma palavra-chave
    (padrão: "hood" — pensado pra pegar tokens pareados com HOOD na Arbitrum),
    dispara um alarme sonoro: 8 bipes de 888Hz, 888ms cada, por padrão

Uso:
  python gu_alert.py                       # checa a cada 5s, alerta p/ "hood"
  python gu_alert.py --interval 3          # checa a cada 3s
  python gu_alert.py --watch hood robin    # mais de uma palavra-chave
  python gu_alert.py --beep-times 5 --beep-freq 660 --beep-ms 300

Instalar dependência:
  pip install requests
"""

import argparse
import math
import os
import platform
import re
import struct
import subprocess
import sys
import tempfile
import time
import wave

try:
    import requests
except ImportError:
    sys.exit("Falta instalar: pip install requests")

REST_URL = "https://api.gu.exchange/metrics/volume"

# chainId -> nome legível. Se aparecer um chainId novo, cai no fallback
# "chain-<id>" e nada quebra.
CHAIN_NAMES = {
    42161: "Arbitrum One",
    42170: "Arbitrum Nova",
    1: "Ethereum",
}

# remove caracteres de controle (ex: sequências de escape de terminal) antes
# de imprimir qualquer texto vindo da API — proteção básica, já que qualquer
# um pode criar um token com nome arbitrário.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def clean(value):
    return _CONTROL_CHARS.sub("", str(value)) if value is not None else ""


def network_name(chain_id):
    return CHAIN_NAMES.get(chain_id, f"chain-{chain_id}")


def extract_tokens(payload):
    """Puxa a lista de tokens de qualquer formato que a API devolver."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("metrics", "tokens", "coins", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def token_key(t):
    return t.get("token") or t.get("address") or t.get("symbol")


def matches_watchlist(t, keywords):
    """Bate por nome, símbolo OU moeda de reserva — pega tanto um token
    chamado 'hood' quanto um token qualquer pareado com HOOD."""
    haystack = " ".join([
        str(t.get("symbol", "")),
        str(t.get("name", "")),
        str(t.get("reserveSymbol", "")),
    ]).lower()
    return any(k.lower() in haystack for k in keywords)


# ─────────────────────────── ALARME SONORO ────────────────────────────
def _tone_wav_bytes(freq, duration_ms, sample_rate=44100, amplitude=28000):
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray()
    for i in range(n_samples):
        value = int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
        buf += struct.pack("<h", value)
    return bytes(buf), sample_rate


def _play_wav_unix(path):
    for player in ("afplay", "paplay", "aplay"):
        try:
            subprocess.run([player, path], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=5, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return False


def beep(times=8, freq=888, duration_ms=888):
    """Toca `times` bipes de `freq` Hz, `duration_ms` ms cada."""
    if platform.system() == "Windows":
        try:
            import winsound
            for _ in range(times):
                winsound.Beep(freq, duration_ms)
            return
        except Exception:
            pass  # cai pro fallback abaixo

    frames, sample_rate = _tone_wav_bytes(freq, duration_ms)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    try:
        with wave.open(path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)
        for _ in range(times):
            if not _play_wav_unix(path):
                print("\a", end="", flush=True)  # último fallback: bell do terminal
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ─────────────────────────────── SAÍDA ─────────────────────────────────
def print_token(t, hit=False):
    symbol  = clean(t.get("symbol", "???"))
    name    = clean(t.get("name", "???"))
    chain   = network_name(t.get("chainId", 42161))
    address = clean(t.get("token") or t.get("address") or "—")
    creator = clean(t.get("creator", "—"))
    reserve = clean(t.get("reserveSymbol", "ARB"))
    now     = time.strftime("%H:%M:%S")

    tag = "🚨 BATEU NA PALAVRA-CHAVE" if hit else "novo token"
    print(f"\n[{now}] {tag}")
    print(f"  Nome/Symbol : {name} ({symbol})")
    print(f"  Rede        : {chain}")
    print(f"  Endereço    : {address}")
    print(f"  Criador     : {creator}")
    print(f"  Pareado com : {reserve}")
    sys.stdout.flush()


def run(interval, keywords, beep_times, beep_freq, beep_ms):
    print(f"Monitorando {REST_URL} a cada {interval}s...")
    print(f"Palavras-chave de alerta: {', '.join(keywords)}")
    print(f"Alarme: {beep_times}x, {beep_freq}Hz, {beep_ms}ms cada\n")
    seen = set()
    while True:
        try:
            r = requests.get(REST_URL, timeout=10)
            if r.status_code == 200:
                payload = r.json()
                for t in extract_tokens(payload):
                    key = token_key(t)
                    if key and key not in seen:
                        seen.add(key)
                        hit = matches_watchlist(t, keywords)
                        print_token(t, hit=hit)
                        if hit:
                            beep(beep_times, beep_freq, beep_ms)
        except Exception as e:
            print(f"[erro ao consultar API: {e}]")
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Monitor de tokens novos na GU Factory")
    ap.add_argument("--interval", type=int, default=5,
                     help="segundos entre checagens (padrão: 5)")
    ap.add_argument("--watch", nargs="+", default=["hood"],
                     help="palavras-chave a destacar — nome, símbolo ou reserva (padrão: hood)")
    ap.add_argument("--beep-times", type=int, default=8, help="nº de bipes (padrão: 8)")
    ap.add_argument("--beep-freq", type=int, default=888, help="frequência em Hz (padrão: 888)")
    ap.add_argument("--beep-ms", type=int, default=888, help="duração de cada bipe em ms (padrão: 888)")
    args = ap.parse_args()
    try:
        run(args.interval, args.watch, args.beep_times, args.beep_freq, args.beep_ms)
    except KeyboardInterrupt:
        print("\nParado.")