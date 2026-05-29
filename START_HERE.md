# 🚀 START HERE - AI Context Injector Development

## Status: Ready for Design Phase

This repo has been initialized with:
- ✅ Git repository created
- ✅ Directory structure setup
- ✅ MIT license
- ✅ README with project overview
- ✅ OpenSpec change initialized
- ✅ Proposal created (see openspec/changes/initial-release/proposal.md)
- ✅ Reference documentation from hackDark

## What to Do Next

### 1. Read the Proposal
```bash
cat openspec/changes/initial-release/proposal.md
```

Key points:
- Based on 1,473 lines of WORKING code from hackDark
- Performance proven: 17.7ms (8.5x better than target)
- Clear differentiators vs Continue.dev
- 4-week timeline to launch

### 2. Read the Reference
```bash
cat REFERENCE.md
```

This documents:
- What already works in hackDark
- Test results (all passing)
- Anti-hallucination techniques (research-backed)
- Migration strategy from hackDark
- Architecture decisions

### 3. Next Steps in Order

**Today:**
1. Create design.md following OpenSpec workflow
   ```bash
   npx openspec instructions design --change initial-release
   ```

2. Design clean API (remove hackDark coupling)
   - Plugin system for providers
   - Configuration-based setup
   - Framework-agnostic

3. Create specs/ for each capability
   - Tag parsing
   - Context formatting
   - Provider interface
   - Plugin system
   - Core injector

**This Week:**
4. Extract core code from hackDark
   - types.py (no changes)
   - parser.py (no changes)
   - formatter.py (no changes)
   - injector.py (remove auto-detect, make configurable)

5. Create examples/
   - OpenAI integration
   - Anthropic (Claude)
   - Ollama (local LLM)

**Next 2 Weeks:**
6. Documentation
7. Tests
8. PyPI packaging

**Week 4:**
9. Launch prep
10. Publish & announce

## Quick Reference

**Project location:**
```bash
cd ~/Project/ai-context-injector
```

**OpenSpec commands:**
```bash
npx openspec status                           # Check progress
npx openspec instructions design              # Get design template
npx openspec instructions spec:<capability>   # Get spec template
```

**hackDark reference code:**
```bash
cd ~/Project/hackDark/scripts/context/        # Source code
./scripts/context-test "@memory query"        # Test working system
```

**Performance target:**
- ✅ <20ms (currently 17.7ms in hackDark)

## Key Differentiators

Why this will succeed vs Continue.dev:

| Feature | Continue.dev | AI Context Injector |
|---------|--------------|---------------------|
| Project isolation | ❌ Weak | ✅ Hard |
| Anti-hallucination | ~ Basic | ✅ Research-backed (5 rules) |
| Citations | ❌ No | ✅ [memory:project:date] |
| Cross-project | Auto (risky) | ✅ Explicit :all modifier |
| Framework | VSCode only | ✅ Any (OpenAI, Claude, etc) |

## Success Metrics (6 months)

- 🎯 100+ GitHub stars
- 🎯 1,000+ PyPI downloads
- 🎯 5+ external contributors
- 🎯 Featured in AI newsletter
- 🎯 Referenced in blog posts

## Questions?

Everything you need is in:
- `proposal.md` - Why and what
- `REFERENCE.md` - Working code and migration strategy
- `README.md` - Project overview

## Ready to Start?

```bash
# Start new OpenCode chat in this directory
cd ~/Project/ai-context-injector

# First command to AI:
"Read proposal.md and REFERENCE.md. Create design.md following OpenSpec.
Focus on clean API design, plugin system, and removing hackDark coupling.
Use the working code as reference but design from scratch for OSS."
```

Good luck! 🚀
