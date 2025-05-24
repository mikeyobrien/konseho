# Release Checklist

Pre-release verification and preparation steps.

## Code Quality:
- [ ] All tests passing (pytest)
- [ ] Type checking passes (mypy src)
- [ ] Linting clean (ruff check src tests)
- [ ] Code formatted (black src tests)
- [ ] No commented debug code
- [ ] No hardcoded test values

## Documentation:
- [ ] README.md updated with:
  - [ ] Clear value proposition
  - [ ] Installation instructions
  - [ ] Quick start example (<10 lines)
  - [ ] Link to full docs
- [ ] API documentation complete
- [ ] All examples working
- [ ] CHANGELOG.md updated
- [ ] Contributing guide written

## Examples:
- [ ] simple_debate.py runs successfully
- [ ] code_council.py demonstrates multi-step
- [ ] research_council.py shows parallelism
- [ ] human_review.py interaction works
- [ ] All examples have comments

## Performance:
- [ ] Benchmarks meet targets:
  - [ ] <10ms council creation
  - [ ] <100ms step overhead
  - [ ] <10MB memory per agent
- [ ] No memory leaks identified
- [ ] Async execution verified

## Package:
- [ ] Version updated in pyproject.toml
- [ ] Dependencies versions pinned
- [ ] License file included
- [ ] Package builds successfully
- [ ] Import test passes

## Integration:
- [ ] Works with latest Strands SDK
- [ ] Python 3.10+ compatibility
- [ ] No platform-specific code
- [ ] Terminal interface cross-platform

## Security:
- [ ] No secrets in code
- [ ] Safe default permissions
- [ ] Input validation present
- [ ] No eval() or exec() usage

## Repository:
- [ ] .gitignore complete
- [ ] No large files committed
- [ ] CI/CD workflow defined
- [ ] Issue templates created
- [ ] Code of conduct added

## Testing:
- [ ] Fresh install test:
  ```bash
  python -m venv test_env
  source test_env/bin/activate
  pip install git+https://github.com/USER/konseho
  python -c "from konseho import Council"
  ```
- [ ] Run example from fresh install
- [ ] Test on different Python versions
- [ ] Verify error messages helpful

## Final Steps:
1. Tag release: `git tag v0.1.0`
2. Push tag: `git push origin v0.1.0`
3. Create GitHub release with notes
4. Announce in relevant communities
5. Monitor issue tracker

## Post-Release:
- [ ] Monitor for critical issues
- [ ] Respond to user feedback
- [ ] Plan next version features
- [ ] Update project board