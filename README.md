# Token Discovery Alerts

![Language: Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square&logo=python) ![Interface: CLI](https://img.shields.io/badge/Interface-CLI-555555?style=flat-square) [![License: MIT](https://img.shields.io/badge/License-MIT-555555?style=flat-square)](LICENSE)

A small terminal listener for newly observed GU Factory tokens, with keyword matching and configurable local audio alerts.

One Python file polls the configured public metrics endpoint, deduplicates tokens in memory and prints their basic fields. Keywords match the token name, symbol or reserve-currency fields.

## Install and choose alert terms

```console
python -m pip install requests
python listener.py --help
```

Operational example, which starts network polling:

```console
python listener.py --watch demo example --interval 10 --beep-times 2 --beep-freq 880 --beep-ms 200
```

| Option | Effect |
| --- | --- |
| `--watch` | One or more terms to highlight. |
| `--interval` | Seconds between requests. |
| `--beep-times`, `--beep-freq`, `--beep-ms` | Local alert count, frequency and duration. |

There is no database or background service manager. Restarting clears the seen-token set. Audio uses platform-specific helpers, and CLI help does not test endpoint compatibility or sound output. The [implementation](listener.py) is the complete tool; no dedicated test suite or pinned environment is bundled.

**Technology:** Python · requests · argparse · platform-specific audio helpers

Project-authored source: [MIT](LICENSE). Third-party components retain their own notices and terms.
