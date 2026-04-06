
## Installing Python

#### Windows 11 Windows 10 version 2004 or newer with (May 2020 Update, which contains winget) Windows 8.1 (non-ARM architecture) with (May 2020 Update, which contains winget)

```powershell
. .\install-python.ps1
```

#### Linux and MacOS
On macOS or Linux with [Homebrew](https://brew.sh/), run `install-python.sh` (it installs a current Python via Homebrew). On Debian-based distros without Homebrew, install Python 3.10+ with your package manager, then create a venv: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`.

```bash/zsh/csh/sh
chmod +x ./install-python.sh && ./install-python.sh
```

---
