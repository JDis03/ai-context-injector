## ADDED Requirements

### Requirement: Extract code blocks from markdown
The system SHALL detect and extract code blocks from markdown content.

#### Scenario: Fenced code blocks are detected
- **WHEN** content contains ` ```python\nprint("hello")\n``` `
- **THEN** code block is extracted with `{"lang": "python", "code": "print(\"hello\")"}`

#### Scenario: Multiple code blocks are extracted
- **WHEN** content contains 3 fenced code blocks
- **THEN** all 3 blocks are extracted in document order

#### Scenario: Code blocks without language tag
- **WHEN** content contains ` ```\ncode here\n``` ` without language
- **THEN** code block is extracted with `{"lang": "unknown", "code": "code here"}`

### Requirement: Preserve surrounding context for code blocks
The system SHALL capture surrounding text context for each code block.

#### Scenario: Context includes preceding text
- **WHEN** code block is preceded by "Run this command:"
- **THEN** context includes preceding sentence(s) up to 200 characters

#### Scenario: Context includes following text
- **WHEN** code block is followed by "This outputs the results"
- **THEN** context includes following sentence(s) up to 200 characters

#### Scenario: Context respects section boundaries
- **WHEN** code block is at end of markdown section
- **THEN** context does not include text from next section

### Requirement: Index code blocks as separate chunks
The system SHALL create separate chunks for code blocks when `extract_code_blocks=True`.

#### Scenario: Code chunk has type metadata
- **WHEN** code block is extracted and indexed
- **THEN** chunk metadata includes `{"chunk_type": "code", "lang": "python"}`

#### Scenario: Code blocks are searchable independently
- **WHEN** user searches for "nmap command"
- **THEN** results can include code chunks without their parent text chunks

#### Scenario: Code blocks retain parent chunk reference
- **WHEN** code block is extracted from a text chunk
- **THEN** code chunk metadata includes `{"parent_chunk_id": "..."}`

### Requirement: Code extraction is optional
The system SHALL only extract code blocks when explicitly enabled.

#### Scenario: Default behavior does not extract code
- **WHEN** user calls `index(content)` without `extract_code_blocks` parameter
- **THEN** code blocks remain inline in text chunks

#### Scenario: Opt-in extraction
- **WHEN** user calls `index(content, extract_code_blocks=True)`
- **THEN** code blocks are extracted and indexed separately

### Requirement: Support common code fence formats
The system SHALL recognize standard markdown code fence formats.

#### Scenario: Triple backtick fences
- **WHEN** content contains ` ```lang\ncode\n``` `
- **THEN** code block is extracted

#### Scenario: Triple tilde fences
- **WHEN** content contains `~~~lang\ncode\n~~~`
- **THEN** code block is extracted

#### Scenario: Indented code blocks are ignored
- **WHEN** content contains 4-space indented code
- **THEN** code is NOT extracted (only fenced blocks)
