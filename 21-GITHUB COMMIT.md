# Git & VS Code Workflow Instructions

---

## ⚡ QUICK OPTION (Terminal / CLI)

Use these commands in your VS Code terminal (at the bottom) to do everything instantly.

**1. Create and switch to your new branch**
```powershell
git checkout -b "ADDED-Open-Router-Discord-Support"
```

**2. Save (Stage & Commit) your changes**
```powershell
git add .
git commit -m "Implemented OpenRouter and Discord support"
```

**3. Upload to your GitHub**
```powershell
git push -u origin ADDED-Open-Router-Discord-Support
```

**4. Link the Original Author (for future updates)**
```powershell
git remote add ORIGINAL https://github.com/DataDriven661/TrumpTracker.git
```

---

## 🚨 EMERGENCY FIX: "Push Rejected / Secret Detected"

If GitHub blocks your push because it found a key or a file that shouldn't be there (like `.env`), run this exact sequence:

**1. Undo the previous failed commit**
*(This keeps your file changes but resets the history)*
```powershell
git reset --soft HEAD~1
```

**2. Stop tracking the specific file that caused the error**
*(Wrap the name in quotes if it has spaces)*
```powershell
git rm --cached 'FILENAME_GOES_HERE'
```

**3. Stage the safe files again**
```powershell
git add .
```

**4. Commit with a new message**
```powershell
git commit -m "Fixed credentials and ignored secrets file"
```

**5. Push to your branch**
```powershell
git push -u origin ADDED-Open-Router-Discord-Support
```

---

## 📚 VS Code’s Built-In Git+GitHub (GUI Method)

VS Code includes Git support out-of-the-box. You can publish your local folder to GitHub with only a few clicks, directly from the Source Control panel (the fork icon on the left).

### For New Projects
1.  Open your project folder in VS Code.
2.  Click the **Source Control** icon (left sidebar) and select **“Initialize Repository.”**
3.  Type a message in the box, hover over the checkmark, and click **Commit**.
4.  Click **“Publish to GitHub”** (or use `Ctrl+Shift+P` → “Publish to GitHub”).
5.  VS Code handles the rest—your code is now on GitHub.

### For Existing Repos
Simply Open, Edit, Commit, and Push changes all without leaving VS Code.

| Tool | Setup Required | Key Action | Extra Install Needed | Ease of Use |
| :--- | :--- | :--- | :--- | :--- |
| **VS Code (built-in)** | Install Git, login to GitHub | Source Control panel | No | Very easy |

---

## 🔱 How to Push Your Branch & Link the "ORIGINAL" Source

Since you cloned the repo from your own account (your Fork), VS Code already knows about your GitHub (`origin`). Now we need to create a separate branch for your new code and link the Author's repo.

### Step 1: Create Your Branch
Do this **before** you commit your changes so they remain separate from the main code.

1.  Look at the very **bottom-left corner** of VS Code (it likely says `main` or `master`).
2.  Click that name. *(If you don't see it, press `Ctrl+Shift+P` and type `Git: Create Branch`)*.
3.  Select **+ Create new branch...**
4.  Type exactly: `ADDED-Open-Router-Discord-Support`
5.  Press **Enter**.

### Step 2: Commit and Push to YOUR Fork (`origin`)

1.  Go to the **Source Control** tab (the fork icon on the left sidebar).
2.  Type your message (e.g., "Updated tracker.py and env").
3.  Click **Commit**.
4.  Click the blue **Publish Branch** button (this sends this specific branch to your GitHub account).

### Step 3: Add the "ORIGINAL" Remote
Now we link the **Author's** repository so you can verify updates later.

1.  Copy the Author's URL: `https://github.com/DataDriven661/TrumpTracker.git`
2.  In VS Code, press `Ctrl + Shift + P`.
3.  Type and select: **Git: Add Remote**.
4.  It will ask for a name. Type: `ORIGINAL` (Case sensitive).
5.  It will ask for the URL. Paste the URL above.