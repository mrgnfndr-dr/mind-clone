# mind-clone — built clones

Branch `Clones` holds finished mind-clones (the skill lives on `main`). Each folder
under `clones/` is self-contained: clone.db (the brain), raw/ (transcripts),
config.json, runs/.

## Use on another machine
    git clone -b Clones --single-branch https://github.com/mrgnfndr-dr/mind-clone.git mc-clones
    cd mc-clones
    python3 loop.py clones/<slug> chat   # needs the mind-clone skill loop.py

clone.db is SQLite, built on WSL/ext4. On Windows run CHAT from inside WSL to avoid
the wsl.localhost SMB SQLite-lock issue.
