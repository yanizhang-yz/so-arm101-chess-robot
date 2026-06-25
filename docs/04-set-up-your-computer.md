# 4. Set up your computer

We'll install everything you need and check it works — all by copy-pasting. This
page is written for a **Mac**; there are notes for Windows/Linux at the bottom.

If any command gives an error, don't panic — flip to
[Glossary & help](09-glossary-and-help.md). Errors are normal and fixable.

## First, meet the Terminal

The **Terminal** is a plain text window where you type commands to your computer.
It looks old-fashioned, but it's just a way to tell the computer exactly what to
do.

- On a Mac: press **Cmd + Space**, type **Terminal**, press Enter. A window opens.

You type a command, press Enter, and the computer does it. That's the whole game.

## Step A — install "uv" (it manages Python for you)

**Python** is the language our project speaks. **uv** is a little helper that
installs the correct Python and keeps everything tidy. Paste this and press Enter:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close the Terminal and open it again so the change takes effect.

## Step B — go into the project folder

You already have the project — it's the `chess-robot` folder this guide lives in.
Tell the Terminal to go there (adjust the path if yours is elsewhere):

```bash
cd ~/Documents/projects/chess-robot
```

`cd` means "change directory" — i.e. "go into this folder."

## Step C — build the project's workspace

These two commands create a private little Python workspace for the project and
install the project plus its helpers into it:

```bash
uv venv --python 3.12
uv pip install -e . pytest
```

(The workspace is called a **virtual environment**, or *venv* — think of it as a
clean toolbox just for this project, so it never messes with the rest of your
computer.)

## Step D — install Stockfish (the chess brain)

```bash
brew install stockfish
```

If your Mac says `brew: command not found`, you first need **Homebrew** (a free
app installer). Get it from [brew.sh](https://brew.sh), then run the line again.

## Step E — check everything works 🎉

First, run the project's self-tests. You should see something like `25 passed`:

```bash
.venv/bin/python -m pytest -q
```

Now play your very first move against the **pretend arm**:

```bash
.venv/bin/python stage1_demo.py --from e2 --to e4
```

You'll see the pretend arm print each step of picking up the piece on e2 and
setting it down on e4. **That's your robot — pretending, for now.** If you got
here, your computer is fully set up. 🙌

## Windows / Linux notes

- **Windows:** the easiest path is to install "WSL" (Windows Subsystem for Linux),
  which gives you a Linux-style Terminal, then follow the Mac steps inside it.
- **Linux:** the same commands work; install Stockfish with your package manager
  (e.g. `sudo apt install stockfish`) instead of `brew`.

---
Back: [Home](Home.md) · Next: [Step 1 — find a square →](05-step-1-find-a-square.md)
