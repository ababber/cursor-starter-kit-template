# GitHub Template Repository Setup

Two ways to automatically include the Cursor Starter Kit in new GitHub repositories:

## Option 1: GitHub Template Repository (Recommended)

Create a template repository that includes the starter kit, then use GitHub's "Use this template" feature.

### Setup Steps

1. **Create a new repository** with just the starter kit:
   ```bash
   gh repo create cursor-starter-kit-template --public --template=false
   cd cursor-starter-kit-template
   ```

2. **Copy the starter kit** to this repo:
   ```bash
   cp -r /path/to/cursor-starter-kit/* .
   git add -A
   git commit -m "Initial template with Cursor Starter Kit"
   git push
   ```

3. **Enable template mode**:
   - Go to repository Settings → General
   - Check "Template repository"
   - Save

4. **Use the template** when creating new repos:
   - Click "Use this template" button on the template repo
   - Or use: `gh repo create <name> --template <owner/cursor-starter-kit-template>`

### Pros
- ✅ Built into GitHub UI
- ✅ One-click setup
- ✅ Works for all team members
- ✅ No local scripts needed

### Cons
- ❌ Requires maintaining a separate template repo
- ❌ Need to update template when starter kit changes

---

## Option 2: CLI Automation Script

Use the `create-repo-with-kit.sh` script to automate repo creation + installation.

### Setup

1. **Make script executable**:
   ```bash
   chmod +x cursor-starter-kit/create-repo-with-kit.sh
   ```

2. **Create an alias** (optional):
   ```bash
   # Add to ~/.zshrc
   alias new-repo='/path/to/cursor-starter-kit/create-repo-with-kit.sh'
   ```

### Usage

```bash
# Basic usage
./create-repo-with-kit.sh my-project --private --clone

# With description
./create-repo-with-kit.sh my-project --private --description "My awesome project" --clone

# In an organization
./create-repo-with-kit.sh my-project --org my-org --public --clone
```

### What it does

1. Creates GitHub repository via `gh repo create`
2. Clones the repository locally
3. Runs `install.sh` to add starter kit
4. Commits and pushes starter kit files
5. Provides next steps

### Pros
- ✅ Always uses latest starter kit
- ✅ Can customize per repo
- ✅ Works with any repo creation method

### Cons
- ❌ Requires GitHub CLI installed
- ❌ Requires running script manually
- ❌ Two-step process (create + install)

---

## Recommendation

**Use Option 1 (Template Repository)** for:
- Team workflows
- Consistent setup across projects
- One-click creation

**Use Option 2 (CLI Script)** for:
- Custom per-repo configurations
- Always using latest starter kit
- Automation in scripts/workflows

---

## Hybrid Approach

You can use both:
1. Create a template repo for quick starts
2. Use the CLI script when you need customization
3. Update template periodically from main starter kit
