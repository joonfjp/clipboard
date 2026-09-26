<p align="center"><img src="logo.svg" width="72" alt="local clipboard"></p>

# local clipboard

A tiny shared clipboard for your local network. Type or paste something, hit Enter, and grab it from any other device.

## Run

```sh
python3 server.py              # serves on 0.0.0.0:8000
python3 server.py --port 9000  # custom port
```

Then open the printed URL on any device on the same network. No dependencies beyond Python 3.

## Use

- **Enter** saves an entry, **Shift+Enter** adds a new line, **/** jumps to the input
- **Click** an entry to copy it, **right-click** to remove it (the buttons do the same)
- **Clear all** at the top wipes everything (click twice to confirm)
- Entries are stored in `clips.json` (set another path with `--data`) and sync across open tabs every few seconds

> There is no auth. Only run it on networks you trust.
