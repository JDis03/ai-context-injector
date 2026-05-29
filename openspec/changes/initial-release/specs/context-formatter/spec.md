# Specification: Context Formatter

## ADDED Requirements

### Requirement: Format with clear delimiters

The context formatter SHALL wrap all context output with BEGIN/END delimiters for clear boundaries.

#### Scenario: Basic formatting with delimiters

- **WHEN** formatting context items
- **THEN** output starts with "=== BEGIN CONTEXT ===" and ends with "=== END CONTEXT ==="

#### Scenario: Empty context

- **WHEN** formatting empty list of items
- **THEN** returns empty string (no delimiters for zero items)

#### Scenario: Single item with delimiters

- **WHEN** formatting one context item
- **THEN** output includes BEGIN delimiter, item content, and END delimiter

### Requirement: Include anti-hallucination rules

The context formatter SHALL include critical anti-hallucination instructions by default.

#### Scenario: Rules included by default

- **WHEN** formatting with default settings
- **THEN** output includes 5 critical rules after BEGIN delimiter

#### Scenario: Rules can be disabled

- **WHEN** formatting with `include_anti_hallucination_rules=False`
- **THEN** output excludes anti-hallucination rules section

#### Scenario: Rules mention citations

- **WHEN** anti-hallucination rules are included
- **THEN** rules explicitly instruct to use [memory:project:date] format citations

### Requirement: Add metadata for each item

The context formatter SHALL include source, project, relevance, and timestamp metadata for each context item.

#### Scenario: Full metadata included

- **WHEN** formatting with `include_metadata=True` (default)
- **THEN** each item includes "Source: X | Project: Y | Relevance: Z | Date: YYYY-MM-DD"

#### Scenario: Metadata can be disabled

- **WHEN** formatting with `include_metadata=False`
- **THEN** output excludes metadata lines

#### Scenario: Optional file metadata

- **WHEN** item has file_path and line_range
- **THEN** metadata includes "File: path | Lines: X-Y"

### Requirement: Include citations

The context formatter SHALL generate and include citation strings for each context item.

#### Scenario: Memory citation format

- **WHEN** formatting memory item from project "DarkSSH" dated 2026-05-20
- **THEN** citation is "[memory:DarkSSH:2026-05-20]"

#### Scenario: Code citation with file and lines

- **WHEN** formatting code item from "parser.py" lines 10-25
- **THEN** citation is "[code:parser.py:10-25]"

#### Scenario: Session citation with ID

- **WHEN** formatting session item with session_id "abc123"
- **THEN** citation is "[session:abc123:2026-05-29]"

#### Scenario: Citations can be disabled

- **WHEN** formatting with `include_citations=False`
- **THEN** output excludes citation lines

### Requirement: Add cross-project warnings

The context formatter SHALL detect and warn when context items are from different projects than current.

#### Scenario: Single project only

- **WHEN** all items are from current project "DarkKeyboard"
- **THEN** no warning is added

#### Scenario: Cross-project results

- **WHEN** items include results from "DarkSSH" and current is "DarkKeyboard"
- **THEN** warning added: "⚠️ WARNING: Some results are from other projects: DarkSSH"

#### Scenario: Multiple cross-projects

- **WHEN** items from "DarkSSH" and "DarkRDP" with current "DarkKeyboard"
- **THEN** warning lists all cross-projects: "DarkRDP, DarkSSH" (sorted)

#### Scenario: Warning placement

- **WHEN** cross-project warning is added
- **THEN** warning appears after anti-hallucination rules, before context items

### Requirement: Number context items

The context formatter SHALL number each context item sequentially.

#### Scenario: Item numbering

- **WHEN** formatting 3 context items
- **THEN** items are labeled "--- Context Item 1/3 ---", "--- Context Item 2/3 ---", "--- Context Item 3/3 ---"

#### Scenario: Summary header

- **WHEN** formatting N items for project "DarkKeyboard"
- **THEN** includes "Retrieved Context for: DarkKeyboard\nFound N relevant item(s)"

### Requirement: Format content cleanly

The context formatter SHALL ensure item content is properly formatted with whitespace.

#### Scenario: Strip content whitespace

- **WHEN** item content has leading/trailing whitespace
- **THEN** formatted output strips whitespace from content

#### Scenario: Blank line separation

- **WHEN** formatting multiple items
- **THEN** each item is separated by blank line

#### Scenario: Preserve internal formatting

- **WHEN** item content has internal newlines and indentation
- **THEN** internal formatting is preserved

### Requirement: Support compact format

The context formatter SHALL provide compact formatting option for tight token budgets.

#### Scenario: Compact format structure

- **WHEN** using `format_compact(items)`
- **THEN** output has delimiters, citations, and content only (no metadata, no rules)

#### Scenario: Compact numbering

- **WHEN** compact formatting 3 items
- **THEN** items labeled "[1]", "[2]", "[3]" instead of verbose headers

#### Scenario: Compact spacing

- **WHEN** using compact format
- **THEN** minimal blank lines between items

### Requirement: Format single items

The context formatter SHALL support formatting individual context items.

#### Scenario: Single item without delimiters

- **WHEN** calling `format_single(item, include_delimiters=False)`
- **THEN** output has metadata, citation, content but no BEGIN/END delimiters

#### Scenario: Single item with delimiters

- **WHEN** calling `format_single(item, include_delimiters=True)`
- **THEN** output includes BEGIN/END delimiters around single item

### Requirement: Return ContextResponse

The context formatter SHALL return a ContextResponse object with formatted text and metadata.

#### Scenario: Response structure

- **WHEN** formatting items
- **THEN** returns ContextResponse with formatted_context, items, total_found, filtered_count

#### Scenario: Response metrics

- **WHEN** response includes cross-project warning
- **THEN** ContextResponse.cross_project_warning field contains warning text

#### Scenario: Empty response

- **WHEN** formatting empty list
- **THEN** returns ContextResponse with empty formatted_context and zero counts

### Requirement: Support configuration

The context formatter SHALL accept configuration options to customize output.

#### Scenario: Default configuration

- **WHEN** initializing without arguments
- **THEN** include_metadata=True, include_citations=True, include_anti_hallucination_rules=True

#### Scenario: Custom configuration

- **WHEN** initializing with custom boolean flags
- **THEN** formatter respects all configuration flags

#### Scenario: Configuration affects all formats

- **WHEN** configuration sets include_citations=False
- **THEN** both format() and format_single() exclude citations

### Requirement: Handle edge cases

The context formatter SHALL handle edge cases gracefully.

#### Scenario: Very long content

- **WHEN** item content is >10,000 characters
- **THEN** formatter outputs full content without truncation

#### Scenario: Special characters in content

- **WHEN** item content contains markdown, code, or special characters
- **THEN** output preserves special characters exactly

#### Scenario: Empty content string

- **WHEN** item has empty content string
- **THEN** formatter outputs blank line for content (no error)
