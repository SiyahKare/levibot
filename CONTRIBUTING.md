# Contributing to LeviBot

Thank you for your interest in contributing to LeviBot! 🎉

This document provides guidelines for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Branch Naming](#branch-naming)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

---

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the problem, not the person
- Help others learn and grow

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/SiyahKare/levibot.git
cd levibot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment template
cp ENV.example .env

# Run tests
make test

# Start API
make run
```

---

## 🔄 Development Workflow

1. **Fork** the repository
2. **Clone** your fork
3. **Create** a feature branch
4. **Make** your changes
5. **Test** your changes
6. **Commit** with clear messages
7. **Push** to your fork
8. **Open** a Pull Request

---

## 🌿 Branch Naming

Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

**Examples:**
```
feature/webhook-triggers
fix/rate-limit-redis
refactor/lifespan-handlers
docs/architecture-diagram
test/e2e-signals-flow
chore/dependency-updates
```

---

## 💬 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `test`: Test additions/updates
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `style`: Code style changes (formatting)
- `ci`: CI/CD changes

### Examples

```bash
feat(api): add batch signal scoring endpoint

- Implements POST /signals/batch
- Supports parallel processing of multiple signals
- Reduces API calls by 10x for bulk operations

Closes #123

fix(risk): correct ATR calculation for short positions

- ATR multiplier was inverted for sell side
- Added unit tests for both buy/sell scenarios
- Updated risk policy documentation

Fixes #456

docs(readme): add MinIO local stack quick start

- Added setup instructions for local S3
- Included make targets documentation
- Added troubleshooting section
```

---

## 🔀 Pull Request Process

### Before Opening a PR

1. **Sync with main:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run tests:**
   ```bash
   make test
   make e2e  # if applicable
   ```

3. **Check linting:**
   ```bash
   ruff check backend/src/
   ```

4. **Update documentation:**
   - README if API changes
   - Inline comments for complex logic
   - ENV.example if new env vars

### Opening a PR

1. Use the PR template (auto-populated)
2. Fill out all sections
3. Link related issues
4. Add screenshots/logs if applicable
5. Mark as draft if work-in-progress

### Review Process

- At least 1 approval required
- All CI checks must pass
- No merge conflicts
- Documentation updated
- Tests passing

### After Merge

- Delete your feature branch
- Update your fork
- Celebrate! 🎉

---

## 🎨 Code Style

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints (`from __future__ import annotations`)
- Max line length: 120 characters
- Use `ruff` for linting

```python
# Good
def score_signal(text: str, source: str = "telegram") -> dict:
    """Score a trading signal using ML model."""
    result = model.predict(text)
    return {"label": result.label, "confidence": result.confidence}

# Bad
def score_signal(text,source="telegram"):
    result=model.predict(text)
    return {"label":result.label,"confidence":result.confidence}
```

### TypeScript/React

- Use functional components
- Prefer `const` over `let`
- Use TypeScript types (no `any`)
- Format with Prettier

```typescript
// Good
const SignalCard: React.FC<{ signal: Signal }> = ({ signal }) => {
  const [loading, setLoading] = useState(false);
  return <div>{signal.text}</div>;
};

// Bad
function SignalCard(props) {
  var loading = false;
  return <div>{props.signal.text}</div>;
}
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
make test-all

# Unit tests only
make test

# E2E tests
make e2e

# Specific test file
pytest backend/tests/test_risk_engine.py -v

# With coverage
pytest --cov=backend/src --cov-report=html
```

### Writing Tests

- **Unit tests:** Test individual functions/classes
- **Integration tests:** Test component interactions
- **E2E tests:** Test full user workflows

```python
# Unit test example
def test_score_signal_buy():
    result = score_signal("BUY BTCUSDT @ 60000")
    assert result["label"] == "BUY"
    assert 0.0 <= result["confidence"] <= 1.0

# E2E test example
@pytest.mark.e2e
def test_signal_flow_end_to_end(base_url):
    with httpx.Client(base_url=base_url) as client:
        # Ingest signal
        r = client.post("/signals/ingest-and-score", params={"text": "BUY BTC"})
        assert r.status_code == 200
        
        # Verify events
        files = glob.glob("backend/data/logs/*/events-*.jsonl")
        assert any("SIGNAL_SCORED" in open(f).read() for f in files)
```

### Test Coverage

- Aim for 80%+ coverage on core modules
- 100% coverage on risk engine
- E2E tests for critical user flows

---

## 📚 Documentation

### Code Comments

```python
# Good: Explains WHY, not WHAT
# Use ATR-based SL/TP if hints not provided (policy-driven)
sl, tp, meta = derive_sl_tp(side, price, atr, tp_hint, sl_hint)

# Bad: States the obvious
# Call the derive_sl_tp function
sl, tp, meta = derive_sl_tp(side, price, atr, tp_hint, sl_hint)
```

### README Updates

Update README when:
- Adding new API endpoints
- Changing configuration
- Adding new features
- Modifying deployment process

### API Documentation

Document all endpoints:
```python
@app.post("/signals/score")
def score_signal(text: str) -> dict:
    """
    Score a trading signal using ML model.
    
    Args:
        text: Signal text (e.g., "BUY BTCUSDT @ 60000")
    
    Returns:
        {
            "label": "BUY" | "SELL" | "NO-TRADE",
            "confidence": 0.0-1.0,
            "reasons": ["rule:BUY(1)", "ml:BUY(0.82)"]
        }
    
    Example:
        curl -X POST "http://localhost:8000/signals/score?text=BUY%20BTC"
    """
    ...
```

---

## 🐛 Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml):
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs/screenshots

---

## ✨ Requesting Features

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml):
- Problem statement
- Proposed solution
- Use case
- Alternatives considered

---

## 📞 Getting Help

- **Issues:** [GitHub Issues](https://github.com/SiyahKare/levibot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/SiyahKare/levibot/discussions)
- **Email:** [Your contact email]

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

Thank you for contributing to LeviBot! 🚀
