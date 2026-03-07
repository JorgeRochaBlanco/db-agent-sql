# Release Checklist

Complete checklist for releasing a new version of `db-query-agent`.

---

## Pre-Release

### Code Quality

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No failing CI/CD pipelines
- [ ] Code formatted (`black src/ tests/`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] No security vulnerabilities
- [ ] Type hints added where appropriate

### Documentation

- [ ] README.md updated
- [ ] CHANGELOG.md updated with release notes
- [ ] API documentation up to date
- [ ] Integration guides reviewed
- [ ] Examples tested and working
- [ ] Architecture docs current
- [ ] Troubleshooting guide complete

### Version Management

- [ ] Version bumped in `pyproject.toml`
- [ ] Version follows semantic versioning
- [ ] CHANGELOG.md has version entry
- [ ] Migration guide created (if breaking changes)

### Package Configuration

- [ ] `pyproject.toml` complete
- [ ] `setup.py` up to date
- [ ] `MANIFEST.in` includes all files
- [ ] `requirements.txt` current
- [ ] `.gitignore` configured
- [ ] LICENSE file present

---

## Build & Test

### Local Testing

- [ ] Clean virtual environment created
- [ ] Package installs: `pip install -e .`
- [ ] All imports work
- [ ] Basic functionality tested
- [ ] Optional dependencies work
- [ ] Demo app runs

### Build Process

- [ ] Previous builds cleaned: `rm -rf dist/ build/`
- [ ] Package builds: `python -m build`
- [ ] Wheel created (`.whl`)
- [ ] Source distribution created (`.tar.gz`)
- [ ] Twine check passes: `twine check dist/*`
- [ ] Package contents verified

### TestPyPI

- [ ] Uploaded to TestPyPI
- [ ] Installed from TestPyPI
- [ ] Import works from TestPyPI install
- [ ] Basic functionality works
- [ ] Dependencies resolve correctly

---

## Release

### Git

- [ ] All changes committed
- [ ] Working directory clean
- [ ] On correct branch (main/master)
- [ ] Pulled latest changes
- [ ] No merge conflicts

### PyPI

- [ ] PyPI account ready
- [ ] API token configured
- [ ] Package name available
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Package visible on PyPI
- [ ] Installation works: `pip install db-query-agent`

### GitHub

- [ ] Git tag created: `git tag -a v0.1.0 -m "Release v0.1.0"`
- [ ] Tag pushed: `git push origin v0.1.0`
- [ ] GitHub release created
- [ ] Release notes added
- [ ] Distribution files attached
- [ ] Release published

---

## Post-Release

### Verification

- [ ] Package installs from PyPI
- [ ] All features work in fresh install
- [ ] Documentation links work
- [ ] Examples run successfully
- [ ] No critical bugs reported

### Communication

- [ ] Release announcement prepared
- [ ] Social media posts ready
- [ ] Documentation site updated
- [ ] Users notified (if applicable)
- [ ] Changelog published

### Monitoring

- [ ] PyPI download stats checked
- [ ] GitHub issues monitored
- [ ] User feedback collected
- [ ] Bug reports triaged
- [ ] Performance metrics reviewed

---

## Version-Specific Checklists

### Patch Release (0.1.x)

- [ ] Bug fixes only
- [ ] No new features
- [ ] Backward compatible
- [ ] Minimal documentation changes
- [ ] Quick release cycle

### Minor Release (0.x.0)

- [ ] New features added
- [ ] Backward compatible
- [ ] Documentation updated
- [ ] Examples added
- [ ] Migration guide (if needed)

### Major Release (x.0.0)

- [ ] Breaking changes documented
- [ ] Migration guide complete
- [ ] Deprecation warnings added
- [ ] Major documentation update
- [ ] Extended testing period
- [ ] Beta release considered

---

## Emergency Hotfix

If critical bug found after release:

1. [ ] Create hotfix branch
2. [ ] Fix bug
3. [ ] Test thoroughly
4. [ ] Bump patch version
5. [ ] Fast-track release
6. [ ] Notify users immediately
7. [ ] Post-mortem analysis

---

## Rollback Plan

If release has critical issues:

1. [ ] Identify issue severity
2. [ ] Yank release from PyPI (if critical)
3. [ ] Notify users
4. [ ] Prepare hotfix
5. [ ] Document incident
6. [ ] Update processes

---

## Automation Checklist

### GitHub Actions

- [ ] Test workflow configured
- [ ] Release workflow configured
- [ ] PyPI token in secrets
- [ ] Workflows tested
- [ ] Status badges updated

### CI/CD

- [ ] Automated tests run on PR
- [ ] Automated tests run on push
- [ ] Build verification automated
- [ ] Release process automated
- [ ] Notifications configured

---

## Final Checks

Before clicking "Publish":

- [ ] **STOP** - Review everything above
- [ ] Version number correct
- [ ] CHANGELOG accurate
- [ ] Tests passing
- [ ] Documentation complete
- [ ] No known critical bugs
- [ ] Team approval (if applicable)
- [ ] Ready for production

---

## Post-Release Tasks

Within 24 hours:

- [ ] Monitor error reports
- [ ] Check download stats
- [ ] Respond to issues
- [ ] Update documentation site
- [ ] Announce release

Within 1 week:

- [ ] Collect user feedback
- [ ] Plan next release
- [ ] Update roadmap
- [ ] Document lessons learned

---

## Notes

**Current Version:** 0.1.0  
**Next Version:** _____  
**Release Date:** _____  
**Release Manager:** _____

**Special Considerations:**
- 
- 
- 

**Known Issues:**
- 
- 
- 

---

## Sign-Off

- [ ] Code reviewed by: _____
- [ ] Documentation reviewed by: _____
- [ ] Tests verified by: _____
- [ ] Release approved by: _____

**Date:** _____  
**Signature:** _____

---

**Remember:** It's better to delay a release than to ship a broken package!
