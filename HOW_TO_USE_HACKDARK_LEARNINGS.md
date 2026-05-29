# How to Use hackDark Learnings in ai-context-injector

This guide shows you how to access hackDark's implementation learnings when working on ai-context-injector.

---

## 🎯 Quick Start

### Method 1: Read the Document Directly

**In ai-context-injector chat:**
```
User: "Read LEARNINGS_FROM_HACKDARK.md before implementing X"
```

**What OpenCode will see:**
- 635 lines of validated learnings
- What works (performance benchmarks, proven patterns)
- What to avoid (coupling issues, hardcoded config)
- What to test first (CodebaseProvider, SessionProvider)

**When to use:**
- Before designing a feature
- When making architecture decisions
- When unsure about an approach

---

### Method 2: Use Memory System (Advanced)

**Prerequisites:**
```bash
# Check hackDark memory database exists
ls -lh ~/.hackdark/memory.db

# Should show database file with size
```

**In ai-context-injector chat:**
```
User: "@memory:all hackDark performance 17ms"
User: "@memory:all hackDark anti-hallucination format"
User: "@memory:all hackDark provider pattern works"
```

**What happens:**
1. Tag `@memory:all` triggers cross-project search
2. Searches `~/.hackdark/memory.db` across ALL projects
3. Finds hackDark decisions matching your query
4. Formats with delimiters and anti-hallucination rules
5. Injects into context
6. OpenCode uses that info to make decisions

**Example output:**
```
=== BEGIN CONTEXT ===

CRITICAL RULES FOR USING THIS CONTEXT:
1. ONLY cite information that appears in context sections
2. If context is from different project, CLEARLY state which
3. Include source citations [memory:hackDark:date]
4. If unsure or missing, say "I don't have information"
5. NEVER mix information from different projects

⚠️  WARNING: Some results are from other projects: hackDark. 
Current project is ai-context-injector. 
DO NOT confuse information between projects.

Retrieved Context for: ai-context-injector
Found 2 relevant item(s)

--- Context Item 1/2 ---
Source: memory | Project: hackDark | Relevance: 0.85 | Date: 2026-05-29
Citation: [memory:hackDark:2026-05-29]

LEARNINGS_FROM_HACKDARK.md created in ai-context-injector
635-line bridge document. Proven: 17.7ms performance, anti-hallucination 
format, hard isolation. Improve: remove coupling, explicit config. 
Validate: providers in hackDark first.

--- Context Item 2/2 ---
Source: memory | Project: hackDark | Relevance: 0.78 | Date: 2026-05-29
Citation: [memory:hackDark:2026-05-29]

Tag-based retrieval proven in testing
Parser tested with 3 scenarios, all passing. End-to-end: 17.7ms 
performance. Zero false positives. Recommendation: Keep tag-based 
approach, support modifiers (:all, :recent).

=== END CONTEXT ===
```

**When to use:**
- Quick lookups during implementation
- Finding specific decisions ("What did we decide about X?")
- Checking if hackDark already solved a problem
- Validating an approach

---

### Method 3: Search Specific Topics

**Common queries that work:**

```bash
# Performance
@memory:all hackDark performance 17ms keyword matching

# Architecture
@memory:all hackDark provider pattern interface

# Anti-hallucination
@memory:all hackDark delimiters citations format

# Project isolation
@memory:all hackDark project isolation cross-project

# Testing
@memory:all hackDark edge cases empty results

# What NOT to do
@memory:all hackDark coupling hardcoded config

# What to validate first
@memory:all hackDark CodebaseProvider SessionProvider test
```

---

## 📋 Workflow Examples

### Example 1: Designing Provider Interface

**Scenario:** You're about to implement the IContextProvider interface

**Step 1 - Read learnings:**
```
User: "Read LEARNINGS_FROM_HACKDARK.md section 'Provider Pattern'"
```

**Step 2 - Get specifics from memory:**
```
User: "@memory:all hackDark provider interface simple methods"
```

**Step 3 - Implement based on learnings:**
```
User: "Implement IContextProvider using the proven pattern from hackDark.
Keep it simple: 4 methods only (retrieve, is_available, name, source_type)"
```

---

### Example 2: Deciding on Performance Optimization

**Scenario:** Should we use embeddings or keyword matching in v1?

**Query:**
```
User: "@memory:all hackDark embeddings keyword matching performance"
```

**Response from memory:**
```
Citation: [memory:hackDark:2026-05-29]
Keyword matching: 17.7ms (8.5x better than 150ms target)
Recommendation: Ship v1 with keywords, add embeddings in v1.1
Rationale: KISS principle, can add later without breaking API
```

**Decision:**
```
User: "Based on hackDark learnings, implement keyword matching for v1.
Document embeddings as plugin example for v1.1"
```

---

### Example 3: Avoiding Known Issues

**Scenario:** You're implementing configuration

**Query:**
```
User: "@memory:all hackDark hardcoded config auto-detection"
```

**Response:**
```
Citation: [memory:hackDark:2026-05-29]
Problem: Hardcoded paths only work on one machine
Problem: Auto-detection fragile, not portable
Recommendation: Require explicit configuration, no magic defaults
```

**Decision:**
```
User: "Don't auto-detect like hackDark did. Require explicit config.
Make project parameter required. Fail fast with clear errors."
```

---

### Example 4: Validating Before Shipping

**Scenario:** Should we include CodebaseProvider in v1?

**Query:**
```
User: "@memory:all hackDark CodebaseProvider stub not tested"
```

**Response:**
```
Citation: [memory:hackDark:2026-05-29]
Status: Designed but NOT implemented in hackDark
What we DON'T know: chunk strategy, context size, cache strategy
Recommendation: Implement in hackDark FIRST, test, then port
WARNING: Don't ship unvalidated
```

**Decision:**
```
User: "Don't include CodebaseProvider in v1.0.
Wait for hackDark validation first. Ship examples only."
```

---

## 🔍 Tips for Effective Queries

### Good Queries (Specific)
```
✅ @memory:all hackDark anti-hallucination 5 rules delimiter
✅ @memory:all hackDark performance 17ms benchmark
✅ @memory:all hackDark provider interface 4 methods
✅ @memory:all hackDark project isolation cross-project warning
```

### Bad Queries (Too Vague)
```
❌ @memory:all hackDark
❌ @memory:all context
❌ @memory:all provider
❌ @memory:all performance
```

**Why bad?**
- Too generic, will match too much unrelated content
- No specific keywords to filter by
- Results will be low relevance

### Best Practice
Include 3-4 specific keywords that identify what you're looking for:
- Feature name: "provider", "parser", "formatter"
- Specific detail: "17ms", "delimiter", "isolation"
- Context: "hackDark", "proven", "tested"

---

## 🧪 Testing the Memory System

### Verify it works:

**Step 1 - Check database:**
```bash
ls -lh ~/.hackdark/memory.db
# Should exist and have size
```

**Step 2 - Test search:**
```bash
cd ~/Project/hackDark
./scripts/context-test "@memory:all hackDark LEARNINGS"
```

**Expected output:**
```
Performance: ~18ms
Total found: 1-3
After filtering: 1-3

=== BEGIN CONTEXT ===
[Shows hackDark decisions about LEARNINGS document]
=== END CONTEXT ===
```

**Step 3 - Use in ai-context-injector chat:**
```
User: "@memory:all hackDark performance benchmark"
```

**Should retrieve:**
- 17.7ms performance data
- Keyword matching benchmarks
- Performance recommendations

---

## 📚 What's in hackDark Memory

### Currently Documented:
- ✅ LEARNINGS_FROM_HACKDARK.md created (bridge document)
- ✅ Context injection implementation (1,473 lines)
- ✅ Performance benchmarks (17.7ms proven)
- ✅ WAL mode decision (concurrency improvement)
- ✅ Tag-based retrieval validation
- ✅ Anti-hallucination format proven

### Will Be Added as hackDark Develops:
- CodebaseProvider learnings (when tested)
- SessionProvider learnings (when tested)
- Edge cases discovered in daily use
- Performance optimizations attempted
- Integration patterns validated
- User feedback from real usage

---

## 🔄 Keeping Learnings Updated

### When to Update LEARNINGS_FROM_HACKDARK.md:

**After major implementations:**
```bash
cd ~/Project/hackDark
# Test feature thoroughly
# Document learnings

cd ~/Project/ai-context-injector
# Update LEARNINGS_FROM_HACKDARK.md with:
# - What worked
# - What didn't work
# - Recommendations for library

git commit -m "Update learnings: CodebaseProvider tested"
```

**After discovering edge cases:**
```bash
# Add to "Edge Cases Found in Testing" section
# Include: What happened, how fixed, recommendation
```

**After performance tuning:**
```bash
# Update "Performance Benchmarks" section
# Include: Before/after numbers, what changed, whether worth it
```

---

## 🎯 Golden Rules

1. **Read LEARNINGS first** - Don't guess, use proven patterns
2. **Use @memory:all** - Let the system tell you what hackDark learned
3. **Cite sources** - Always reference [memory:hackDark:date]
4. **Don't cargo cult** - Understand WHY hackDark did something
5. **Validate unknowns** - If hackDark hasn't tested it, don't ship it
6. **Update continuously** - As hackDark learns, update the document

---

## 🚀 Success Checklist

Before implementing a feature in ai-context-injector:

- [ ] Read relevant LEARNINGS_FROM_HACKDARK.md section
- [ ] Query @memory:all for specific decisions
- [ ] Check if hackDark has tested this
- [ ] If tested: use proven pattern
- [ ] If not tested: mark as TODO for hackDark
- [ ] Document your implementation for future reference

---

## 📞 When You're Stuck

If you can't find what you need:

1. **Search broader:**
   ```
   @memory:all hackDark <topic>
   ```

2. **Read full document:**
   ```
   Read LEARNINGS_FROM_HACKDARK.md
   ```

3. **Check source code:**
   ```
   Read ~/Project/hackDark/scripts/context/<file>.py
   ```

4. **Test in hackDark:**
   ```bash
   cd ~/Project/hackDark
   ./scripts/context-test "@memory query"
   # See what actually happens
   ```

5. **Document the gap:**
   ```bash
   # Add TODO to LEARNINGS_FROM_HACKDARK.md
   # Test in hackDark first before implementing in library
   ```

---

**Remember:** hackDark is the laboratory. ai-context-injector is the product.

Test in hackDark → Learn → Document → Build clean in ai-context-injector
