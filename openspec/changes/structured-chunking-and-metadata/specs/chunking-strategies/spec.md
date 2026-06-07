## ADDED Requirements

### Requirement: Pluggable chunking strategies
The system SHALL support multiple chunking strategies that can be selected at index time.

#### Scenario: Default strategy is by_size
- **WHEN** user calls `index(content)` without specifying strategy
- **THEN** system uses `by_size` chunking strategy with default chunk size

#### Scenario: User selects by_markdown_headers strategy
- **WHEN** user calls `index(content, chunking_strategy="by_markdown_headers")`
- **THEN** system splits content on markdown headers (##) and creates one chunk per section

#### Scenario: User selects by_paragraph strategy
- **WHEN** user calls `index(content, chunking_strategy="by_paragraph")`
- **THEN** system splits content on double newlines and creates one chunk per paragraph

### Requirement: Markdown header chunking preserves section titles
The system SHALL preserve section titles when chunking by markdown headers.

#### Scenario: Section title is included in chunk metadata
- **WHEN** content contains `## Reconnaissance\nContent here...`
- **THEN** chunk metadata includes `{"section": "Reconnaissance"}`

#### Scenario: Nested headers create hierarchical sections
- **WHEN** content contains `## Parent\n### Child\nContent...`
- **THEN** chunk metadata includes `{"section": "Parent > Child"}`

### Requirement: Chunking strategy is stored in metadata
The system SHALL automatically store the chunking strategy used in document metadata.

#### Scenario: Strategy is retrievable after indexing
- **WHEN** user indexes with `chunking_strategy="by_markdown_headers"`
- **THEN** document metadata includes `{"chunking_strategy": "by_markdown_headers"}`

### Requirement: Chunks respect maximum size limits
The system SHALL enforce maximum chunk size even when using structural chunking.

#### Scenario: Large section is split when exceeding max size
- **WHEN** markdown section exceeds `max_chunk_size` parameter
- **THEN** section is split into multiple chunks while preserving section metadata

#### Scenario: Max size is configurable per strategy
- **WHEN** user calls `index(content, chunking_strategy="by_markdown_headers", max_chunk_size=2000)`
- **THEN** no chunk exceeds 2000 characters
