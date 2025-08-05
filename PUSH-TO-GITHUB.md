# 🚀 Push to GitHub - Manual Steps

Your repository is created at: https://github.com/Camier/SPOTS

## Option 1: Using Personal Access Token

1. Check if your token is still valid:
   ```bash
   pass show github/api/personal-access-token
   ```

2. If valid, push with:
   ```bash
   TOKEN=$(pass show github/api/personal-access-token | head -1)
   git push https://Camier:${TOKEN}@github.com/Camier/SPOTS.git main
   ```

3. If token is expired, create a new one:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Give it 'repo' scope
   - Copy the token
   - Update in pass: `pass edit github/api/personal-access-token`

## Option 2: Using SSH

1. Add your SSH key to ssh-agent:
   ```bash
   ssh-add ~/.ssh/id_ed25519
   ```

2. Push with SSH:
   ```bash
   git push -u origin main
   ```

## Option 3: GitHub CLI

If you have `gh` CLI installed:
```bash
gh auth login
git push -u origin main
```

## What Gets Pushed

Your commit includes:
- 🗺️ Complete map validation framework
- 🌲 Forest overlay with IGN FORESTINVENTORY.V2
- 🔥 Heatmap visualization with Leaflet.heat
- ☀️ Sun/shadow calculator with SunCalc
- 🧪 97 files total

## After Pushing

1. Visit https://github.com/Camier/SPOTS
2. Add topics: `puppeteer`, `leaflet`, `map-validation`, `geospatial`
3. Consider enabling GitHub Actions for CI/CD
4. Add a star ⭐ to your own repo!

Good luck! 🎉