#!/usr/bin/env python3
"""
create_privatekey_from_prefixes.py

Autor:      Marcin Dobruk <marcin@dobruk.pl>
Utworzono:  2025-08-03
Wersja:     0.1.5
Licencja:   MIT
Opis:
    Generuje pary klucz-adres (WIF + adres BitcoinSV) dla listy prefiksów vanity.
    Prefiksy podaje się jako pojedynczy argument w formacie:
      P1,P2,P3 (bez nawiasów)
      lub
      "P1; P2; P3" (z dowolnymi separatorami).
    Wyświetla status co zadany odstęp prób (domyślnie co 100k) w formacie:
      [STATUS] 300000 prób | 12.5s | ~24000 addr/s
    Po znalezieniu każdego adresu wypisuje wyróżniony wynik (czarne litery na białym tle):
      ✔️ Prefiks P → adres 1XYZ… po N prób (tCzas)
    oraz zapisuje dane do katalogu nadrzędnego `walletsbsv/vanity_wallets`.
    Czyści ekran konsoli na początku, wyświetla wyróżniony nagłówek
    i dodaje pustą linię przed uruchomieniem głównej akcji.
Zależności:
    • Python ≥3.7
    • biblioteka bitsv (pip install bitsv)
Przykład:
    python create_privatekey_from_prefixes.py ZUKU,BSV,GKS
    python create_privatekey_from_prefixes.py "ZUKU; BSV; GKS" 50000
"""
import os
import sys
import json
import secrets
import bitsv
import time
import re
from pathlib import Path

# Funkcja czyszcząca ekran terminala
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Katalog, w którym zostaną zapisane pliki JSON z kluczami
OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'walletsbsv' / 'vanity_wallets'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_duration(seconds: float) -> str:
    """Formatuje czas w sekundach do czytelnego formatu."""
    sec = int(seconds)
    years, sec = divmod(sec, 365*24*3600)
    days, sec = divmod(sec, 24*3600)
    hours, sec = divmod(sec, 3600)
    minutes, sec = divmod(sec, 60)
    parts = []
    if years:
        parts.append(f"{years}y")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{sec}s")
    return ' '.join(parts)


def save_to_file(address: str, key_wif: str, name: str = ""):
    """Zapisuje dane do pliku walletbsv-[address].json w katalogu VANITY_WALLETS."""
    filename = OUTPUT_DIR / f"walletbsv-{address}.json"
    data = {
        "key_wif": key_wif,
        "new_address": address,
        "name": name
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Zapisano do: {filename}")


def generate_vanity_list(prefixes, status_interval=100_000):
    """Generuje adresy dla listy prefiksów vanity, pokazując status i zapisując pliki."""
    targets = ['1' + p for p in prefixes]
    found = {}
    tries = 0
    start = time.perf_counter()

    print(f"Szukam adresów dla: {prefixes} (status co {status_interval:,} prób)...")
    while len(found) < len(prefixes):
        tries += 1
        rand_hex = secrets.token_hex(32)
        key = bitsv.PrivateKey.from_hex(rand_hex)
        addr = key.address

        for prefix, target in zip(prefixes, targets):
            if prefix not in found and addr.startswith(target):
                elapsed = time.perf_counter() - start
                found[prefix] = True
                # Wyróżniony wynik czarne litery na białym tle
                print(f"\n\033[47m\033[30m✔️ Prefiks {prefix} → adres {addr} po {tries:,} próbach ({format_duration(elapsed)})\033[0m")
                save_to_file(addr, key.to_wif())

        if tries % status_interval == 0:
            elapsed = time.perf_counter() - start
            rate = int(tries / elapsed) if elapsed > 0 else 0
            print()
            print(f"[STATUS] {tries:,} prób | {format_duration(elapsed)} | ~{rate:,} addr/s | znaleziono: {len(found)}/{len(prefixes)}")

    total_elapsed = time.perf_counter() - start
    print(f"\nWszystkie prefiksy znalezione w {format_duration(total_elapsed)}.")


if __name__ == '__main__':
    # Czyścimy ekran konsoli
    clear_screen()
    # Wyróżniony nagłówek: czarne litery na białym tle
    header = "create_privatekey_from_prefixes.py v0.1.5 — BSV Vanity Generator: generuje pary klucz-adres dla podanych prefiksów vanity"
    print(f"\033[47m\033[30m{header}\033[0m")
    # Pusta linia przed główną logiką
    print()

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Użycie: python create_privatekey_from_prefixes.py <PREFIX_LIST> [status_interval]")
        sys.exit(1)

    raw = sys.argv[1].strip().strip('"').strip("'")
    prefixes = [p.strip() for p in re.split(r'[;,]+', raw) if p.strip()]

    if not prefixes:
        print("Błąd: lista prefiksów jest pusta.")
        sys.exit(1)
    for p in prefixes:
        if not p.isalnum():
            print(f"Błąd: prefiks '{p}' musi być alfanumeryczny.")
            sys.exit(1)

    try:
        interval = int(sys.argv[2]) if len(sys.argv) == 3 else 100_000
    except ValueError:
        print("Błąd: status_interval musi być liczbą całkowitą.")
        sys.exit(1)

    generate_vanity_list(prefixes, status_interval=interval)
