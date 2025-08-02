#!/usr/bin/env python3
"""
create_privatekey_from_prefix.py

Autor:      Marcin Dobruk <marcin@dobruk.pl>
Utworzono:  2025-08-02
Wersja:     0.1.0
Licencja:   MIT
Opis:
    Generuje parę klucz-adres (WIF + adres BitcoinSV) z żądanym
    prefiksem vanity. Prefix podajemy jako argument z linii poleceń.
    Wyświetla też status co zadany odstęp prób (domyślnie co 100k).
Zależności:
    • Python ≥3.7
    • biblioteka bitsv (pip install bitsv)
Changelog:
    0.1.0 – Wersja początkowa
Przykład:
    python create_privatekey_from_prefix.py ZUKU
wynik:
    Szukam adresu zaczynającego się od '1ZUKU'...
    [STATUS] 300000 prób | 12.5s | ~24000 addr/s
    ...
    {"key_wif": "...", "new_address": "1ZUKU...", "tries": 415123}
"""
import sys
import json
import secrets
import bitsv
import time

def generate_vanity(prefix: str, status_interval: int = 100_000):
    """Generuje adres zaczynający się od prefix (z wiodącym '1') i pokazuje status."""
    target = '1' + prefix
    tries = 0
    start = time.perf_counter()

    while True:
        tries += 1
        # losowy klucz prywatny (32 bajty hex)
        rand_hex = secrets.token_hex(32)
        key = bitsv.PrivateKey.from_hex(rand_hex)
        addr = key.address

        if addr.startswith(target):
            elapsed = time.perf_counter() - start
            output = {
                "key_wif": key.to_wif(),
                "new_address": addr,
                "tries": tries,
                "elapsed_sec": round(elapsed, 2),
                "rate_addr_per_sec": int(tries / elapsed)
            }
            print(json.dumps(output, indent=4))
            return

        # Wyświetl status co `status_interval` prób
        if tries % status_interval == 0:
            elapsed = time.perf_counter() - start
            rate = tries / elapsed if elapsed > 0 else 0
            print(f"[STATUS] {tries:,} prób | {elapsed:.1f}s | ~{int(rate):,} addr/s", end='\r', flush=True)

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Użycie: python create_privatekey_from_prefix.py <PREFIX> [status_interval]")
        sys.exit(1)

    prefix_arg = sys.argv[1].strip()
    if not prefix_arg.isalnum():
        print("Błąd: Prefiks musi być ciągiem alfanumerycznym.")
        sys.exit(1)

    # Opcjonalny interwał statusu
    try:
        interval = int(sys.argv[2]) if len(sys.argv) == 3 else 100_000
    except ValueError:
        print("Błąd: status_interval musi być liczbą całkowitą.")
        sys.exit(1)

    print(f"Szukam adresu zaczynającego się od '1{prefix_arg}' (status co {interval:,} prób)...")
    generate_vanity(prefix_arg, status_interval=interval)
