# Token Discovery Alerts

A small Python polling tool for detecting newly observed tokens and emitting configurable local audio alerts.

## Features

- Polling extracts token lists from supported response envelopes.
- Keyword matching checks token name, symbol and reserve currency.
- Terminal sanitization removes control characters from untrusted labels.

## Stack

Python · requests · argparse · platform-specific audio helpers

Seen-token state is held by the running process; no database or durable resume store is declared.

## Getting started

Create an isolated Python environment and install requests. Use python listener.py --help to inspect arguments; the operational entrypoint polls an external endpoint.

## How it works

```text
Public metrics endpoint → token extraction/deduplication → keyword match → terminal/audio notification
```

## Current limitations

This is a small single-file utility. It has no dedicated test suite or pinned dependencies. Endpoint behavior and audio support were not tested here.

## License

No open-source license has been granted. Redistribution terms remain to be defined.
