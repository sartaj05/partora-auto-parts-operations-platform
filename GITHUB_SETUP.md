# GitHub-ready repository

This ZIP contains the real `.git` directory and the project is already on the `main` branch. It also includes a GitHub Actions workflow at `.github/workflows/ci.yml` that checks Django migrations and builds the React frontend on pushes and pull requests.

## Publish to your GitHub account

Create an empty repository in GitHub, then from the extracted Partora folder run:

```bash
git remote add origin https://github.com/YOUR-USER/YOUR-REPO.git
git push -u origin main
```

If the remote already exists, replace it instead:

```bash
git remote set-url origin https://github.com/YOUR-USER/YOUR-REPO.git
git push -u origin main
```

No hosted GitHub remote is embedded in the ZIP because repository ownership and credentials must come from your GitHub account. The local Git history is complete and ready to push.
