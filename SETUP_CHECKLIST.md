# ReadingView - Setup Checklist

Use this checklist to set up your local development environment and deployment pipeline.

## ✅ Local Development Setup

### Prerequisites
- [ ] Python 3.11+ installed
- [ ] pip installed
- [ ] Git installed
- [ ] Audiobookshelf running and accessible
- [ ] Audiobookshelf API token generated

### Project Setup
- [ ] Clone repository
  ```bash
  git clone https://github.com/yourusername/readingview.git
  cd readingview
  ```

- [ ] Create virtual environment
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  ```

- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Create .env file
  ```bash
  cp .env.example .env
  ```

- [ ] Edit .env with your credentials
  ```env
  ABS_URL=https://your-audiobookshelf-url
  ABS_TOKEN=your_api_token
  ```

- [ ] Test run
  ```bash
  streamlit run app.py
  ```

- [ ] Verify in browser: http://localhost:8501

### Troubleshooting
- [ ] If "No module named 'api'" error:
  - Verify `__init__.py` exists in: `api/`, `components/`, `utils/`
  - Run from project root directory

- [ ] If connection fails:
  - Test Audiobookshelf: `curl $ABS_URL/api/ping`
  - Verify API token is valid
  - Check firewall/network

## ✅ GitHub Actions + Docker Hub Setup

### Docker Hub
- [ ] Create Docker Hub account at https://hub.docker.com
- [ ] Log in to Docker Hub
- [ ] Generate Access Token:
  - Profile → Account Settings → Security
  - New Access Token → Name: `github-actions`
  - Permissions: Read & Write
  - **Save the token!** (shown only once)

### GitHub Repository
- [ ] Create GitHub repository: `readingview`
- [ ] Add GitHub Secrets (Settings → Secrets → Actions):
  - [ ] `DOCKERHUB_USERNAME` = your Docker Hub username
  - [ ] `DOCKERHUB_TOKEN` = the token from above

### Update Repository URLs
- [ ] Edit `unraid-template.xml`:
  - Replace `yourusername` with your GitHub username (4 places)
  
- [ ] Commit all files
  ```bash
  git add .
  git commit -m "Initial commit"
  ```

- [ ] Add remote and push
  ```bash
  git remote add origin https://github.com/yourusername/readingview.git
  git push -u origin main
  ```

- [ ] Verify GitHub Actions:
  - GitHub → Actions tab
  - Should see workflow running
  - Wait for green checkmark

- [ ] Verify Docker Hub:
  - Docker Hub → Repositories
  - Should see `yourusername/readingview`
  - Should have `latest` tag

## ✅ Unraid Setup

### Install Container
- [ ] Open Unraid web interface
- [ ] Docker tab → Add Container
- [ ] Template URL:
  ```
  https://raw.githubusercontent.com/yourusername/readingview/main/unraid-template.xml
  ```
  (Replace `yourusername` with yours!)

- [ ] Configure required fields:
  - [ ] **ABS_URL**: Your Audiobookshelf server URL
  - [ ] **ABS_TOKEN**: Your API token

- [ ] Optional settings:
  - [ ] APP_TITLE (default: ReadingView)
  - [ ] CACHE_TTL (default: 300)
  - [ ] ITEMS_PER_ROW (default: 5)

- [ ] Click Apply

- [ ] Wait for container to start

- [ ] Access ReadingView:
  ```
  http://[unraid-ip]:8501
  ```

- [ ] Verify:
  - [ ] Connection successful
  - [ ] Library shows books
  - [ ] Statistics display correctly

## ✅ Development Workflow

### Daily Development
- [ ] Activate virtual environment
  ```bash
  source venv/bin/activate
  ```

- [ ] Run app
  ```bash
  streamlit run app.py
  ```

- [ ] Make changes in your editor

- [ ] Test in browser (auto-reloads)

- [ ] Commit when ready
  ```bash
  git add .
  git commit -m "Description of changes"
  git push
  ```

- [ ] Wait for GitHub Actions build (~2-5 minutes)

- [ ] Update Unraid:
  - Docker tab
  - Find ReadingView
  - Force Update
  - Apply

## ✅ Verification Tests

### Local Testing
- [ ] App starts without errors
- [ ] Connection to Audiobookshelf works
- [ ] Library tab displays books
- [ ] Book covers load
- [ ] Progress bars show correctly
- [ ] Statistics tab displays
- [ ] Charts render properly
- [ ] No console errors

### Production Testing (Unraid)
- [ ] Container starts successfully
- [ ] Web UI accessible
- [ ] Connection works
- [ ] All features functional
- [ ] Performance acceptable

## 📝 Quick Reference

### Start Development
```bash
cd readingview
source venv/bin/activate
streamlit run app.py
```

### Push Changes
```bash
git add .
git commit -m "Your message"
git push
```

### Update Unraid
1. Docker tab
2. Force Update
3. Apply

### Access URLs
- **Local**: http://localhost:8501
- **Unraid**: http://[unraid-ip]:8501
- **GitHub**: https://github.com/yourusername/readingview
- **Docker Hub**: https://hub.docker.com/r/yourusername/readingview

## 🆘 Common Issues

### "Module not found" Error
- Ensure `__init__.py` files exist
- Run from project root
- Check virtual environment is activated

### Connection Failed
- Verify ABS_URL is accessible
- Test API token
- Check firewall rules

### GitHub Actions Fails
- Check secrets are set correctly
- Verify Docker Hub token is valid
- Look at error logs in Actions tab

### Docker Image Not Found
- Wait for GitHub Actions to complete
- Check Docker Hub for image
- Verify repository name is correct

## ✅ Final Checklist

- [ ] Local development working
- [ ] GitHub repository created
- [ ] Docker Hub configured
- [ ] GitHub Actions building images
- [ ] Unraid container running
- [ ] All features tested
- [ ] Documentation read

## 🎉 You're Done!

Your setup is complete. You can now:
1. Develop locally with instant feedback
2. Push to GitHub for automatic Docker builds
3. Update Unraid with one click
4. Enjoy your audiobook statistics!

## 📚 Documentation

- **[README.md](README.md)** - Quick overview
- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Detailed dev guide
- **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)** - CI/CD setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - All deployment options

---

Need help? Check the documentation or open a GitHub issue.
