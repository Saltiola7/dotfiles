# Chezmoi Dotfiles Setup & Migration Guide

## Overview
We have successfully migrated your dotfiles from a manual symlink script (`sync.sh`) to **Chezmoi**, a modern dotfile manager. This transition provides:
1.  **Security:** Sensitive files (SSH keys, API credentials) are now **encrypted** using `age`. They can be safely stored in a Git repository.
2.  **Portability:** You can set up a new machine with a single command.
3.  **Safety:** No more broken symlinks. Changes are tracked in a dedicated Git repository at `~/.local/share/chezmoi`.

---

## 1. Where is everything?

*   **Source of Truth:** `~/.local/share/chezmoi/`
    *   This is a Git repository.
    *   Your config files live here.
    *   *Secrets* are stored here as encrypted text files.
*   **Master Key:** `~/.config/chezmoi/key.txt`
    *   **CRITICAL:** This is the key to decrypt your secrets. **Back this up to a password manager immediately.**
*   **Destination:** `~/` (Your Home Directory)
    *   Chezmoi generates the actual files here (e.g., `~/.zshrc`) based on the source.

---

## 2. Daily Workflow

### Editing a file
Do not edit `~/.zshrc` directly. Instead:
```bash
# 1. Edit the source file
chezmoi edit ~/.zshrc

# 2. Review changes
chezmoi diff

# 3. Apply changes to your home directory
chezmoi apply
```

### Adding a new file
```bash
# 1. Add the file (Chezmoi will copy content and ignore symlinks)
chezmoi add ~/.newconfig

# 2. (Optional) If it contains secrets, encrypt it
chezmoi add --encrypt ~/.my_secret_file
```

### Committing changes
Since your config is just a Git repo:
```bash
cd ~/.local/share/chezmoi
git add .
git commit -m "Updated dotfiles"
git push
```

---

## 3. Pushing to GitHub (First Time Setup)

Your dotfiles are now in a **new, separate Git repository** located at `~/.local/share/chezmoi`. You need to publish this to GitHub. We recommend a **private** repository since it contains (encrypted) personal data.

**Using GitHub CLI (`gh`):**

```bash
# 1. Go to the source directory
cd ~/.local/share/chezmoi

# 2. Create a new private repository called 'dotfiles' and push
gh repo create dotfiles --private --source=. --push
```

---

## 4. Deploying to a New Machine (The Bootstrap Process)

To set up your environment on a fresh laptop, follow these steps. Note that because your secrets are encrypted, you must manually "bootstrap" the master key before Chezmoi can fully configure the system.

### Step 1: Install Core Tools
```bash
# Install Chezmoi and Age (encryption tool)
brew install chezmoi age
```

### Step 2: Restore the Master Key (The Only Manual Step)
Since your Git repository does not (and should not) contain the decryption key, you must manually inject it from your backup (e.g., Strongbox).
1.  Open your password manager and copy the contents of `key.txt`.
2.  On the new machine, create the identity file:
    ```bash
    mkdir -p ~/.config/chezmoi
    # Paste your key content into this file
    nano ~/.config/chezmoi/key.txt
    chmod 600 ~/.config/chezmoi/key.txt
    ```

### Step 3: Initialize & Apply
Now that the key is in place, Chezmoi can successfully decrypt your SSH keys and environment variables during initialization.
```bash
# Replace 'yourusername' with your actual GitHub username
chezmoi init --apply git@github.com:yourusername/dotfiles.git
```
*Note: If SSH is not yet set up, use the HTTPS URL for the repository initially.*

**During `chezmoi init`, you will be prompted for variables (e.g., `machine_type`).**
- For **MacBook**, use `macbook`.
- For **Mac Mini**, use `mac-mini`.

### Step 4: Reconciliation (Crucial for Mac Mini)
After applying, you might find that some local configurations on the Mac Mini (which were not in `sysAdmin`) differ from what Chezmoi applied (which is currently tuned for your MacBook).

1.  **Review Differences:**
    Run `chezmoi diff` to see if there are any lingering differences between the repo and your local files.
2.  **Add/Merge Local Configs:**
    If you have a local file on Mac Mini that you want to keep/merge:
    ```bash
    chezmoi add ~/.some_local_config
    ```
    If it needs to be different from MacBook, convert it to a template:
    ```bash
    chezmoi chattr +t ~/.some_local_config
    chezmoi edit ~/.some_local_config
    ```
    Then use the `{{ if eq .machine_type "mac-mini" }}` logic to separate the configs.

---

## 5. Security Note regarding the Old Repo
Your old `sysAdmin/dotfiles` directory contained unencrypted secrets.
1.  **Do not use** the old `sysAdmin` repo for dotfiles anymore.
2.  **Verify:** Ensure `sysAdmin/.gitignore` ignores `.env` and `dotfiles/`.
3.  **Cleanup:** You can safely delete the `dotfiles/` and `scripts/` directories once you have confirmed everything is working.

---

## 6. Advanced Topics

### Multiple GitHub Accounts
If you use different email addresses for different projects (e.g., Personal vs. Work), you have two main options:

1.  **Local Config (Recommended):**
    *   Set your global `.gitconfig` (managed by Chezmoi) to your primary email (e.g., `tommi@tommisaltiola.com`).
    *   For specific repositories that need a different email, set it locally:
        ```bash
        cd ~/work/project-repo
        git config user.email "work@email.com"
        ```

2.  **Conditional Includes (Advanced):**
    *   Use Git's `includeIf` directive in your global `.gitconfig` to load a different config file based on the directory path (e.g., `~/work/`).

### Portability & Templating (Mac Mini Migration)
Chezmoi uses the template file `.local/share/chezmoi/.chezmoi.toml.tmpl` to generate your local configuration (`~/.config/chezmoi/chezmoi.toml`).

*   **Machine-Specific Logic:** You can edit this template to automatically set different variables based on the machine you are on.
    ```toml
    [data]
    {{ if eq .chezmoi.hostname "mac-mini" }}
    email = "mini@tommisaltiola.com"
    {{ else }}
    email = "tommi@tommisaltiola.com"
    {{ end }}
    ```
*   **Encryption Config:** The template currently hardcodes the key location to `~/.config/chezmoi/key.txt`. This is good practice for portability; just ensure the key exists at that path on every machine.
