# Specification: Tag Parser

## ADDED Requirements

### Requirement: Parse @memory tags

The tag parser SHALL detect `@memory` tags followed by a query string and extract the tag, query, and position information.

#### Scenario: Basic @memory tag

- **WHEN** user input contains `@memory dark keyboard layout`
- **THEN** parser returns ParsedTag with tag='@memory', query='dark keyboard layout', and correct positions

#### Scenario: Case insensitive tag detection

- **WHEN** user input contains `@MEMORY query text`
- **THEN** parser normalizes tag to lowercase '@memory' and extracts query

#### Scenario: Multiple tags in input

- **WHEN** user input contains `@memory first query and @code second query`
- **THEN** parser returns two ParsedTag objects in order of appearance

### Requirement: Parse @code tags

The tag parser SHALL detect `@code` tags followed by a query string.

#### Scenario: Basic @code tag

- **WHEN** user input contains `@code ContextItem class`
- **THEN** parser returns ParsedTag with tag='@code', query='ContextItem class'

#### Scenario: Code tag with file path

- **WHEN** user input contains `@code parser.py implementation`
- **THEN** parser extracts query as 'parser.py implementation'

### Requirement: Parse @session tags

The tag parser SHALL detect `@session` tags followed by a query string.

#### Scenario: Basic @session tag

- **WHEN** user input contains `@session what did we implement`
- **THEN** parser returns ParsedTag with tag='@session', query='what did we implement'

### Requirement: Parse tag modifiers

The tag parser SHALL support optional modifiers after tags using colon syntax (e.g., `@memory:all`).

#### Scenario: Cross-project modifier

- **WHEN** user input contains `@memory:all emoji implementation`
- **THEN** parser returns ParsedTag with tag='@memory', modifier='all', query='emoji implementation'

#### Scenario: Tag without modifier

- **WHEN** user input contains `@memory query`
- **THEN** parser returns ParsedTag with tag='@memory', modifier=None, query='query'

#### Scenario: Custom modifier

- **WHEN** user input contains `@session:recent last hour`
- **THEN** parser returns ParsedTag with tag='@session', modifier='recent', query='last hour'

### Requirement: Extract query text

The tag parser SHALL extract the query portion of a tag, which is all text following the tag until the next newline or tag.

#### Scenario: Query until newline

- **WHEN** user input contains `@memory query text\nmore text`
- **THEN** parser extracts query as 'query text' (stops at newline)

#### Scenario: Query until next tag

- **WHEN** user input contains `@memory first query @code second query`
- **THEN** first query is 'first query' (stops before @code)

#### Scenario: Query with trailing whitespace

- **WHEN** user input contains `@memory query text   `
- **THEN** parser strips trailing whitespace from query

### Requirement: Handle embedded tags

The tag parser SHALL detect tags embedded within natural language text.

#### Scenario: Tag at beginning

- **WHEN** user input is `@memory keyboard layout for mobile`
- **THEN** parser detects tag and extracts query

#### Scenario: Tag in middle

- **WHEN** user input is `Can you check @memory keyboard and tell me`
- **THEN** parser detects tag and extracts 'keyboard and tell me' as query

#### Scenario: Tag at end

- **WHEN** user input is `Please search @memory recent decisions`
- **THEN** parser detects tag and extracts 'recent decisions'

### Requirement: Return empty list for no tags

The tag parser SHALL return an empty list when no valid tags are found.

#### Scenario: Plain text with no tags

- **WHEN** user input is `This is plain text without tags`
- **THEN** parser returns empty list

#### Scenario: Invalid tag syntax

- **WHEN** user input is `@invalid query`
- **THEN** parser returns empty list (only @memory/@code/@session are valid)

#### Scenario: Tag without query

- **WHEN** user input is `@memory` with no following text
- **THEN** parser returns empty list (query is required)

### Requirement: Provide utility methods

The tag parser SHALL provide utility methods for common operations.

#### Scenario: Check if text has tags

- **WHEN** calling `has_tags("@memory query")`
- **THEN** returns True

#### Scenario: Remove tags from text

- **WHEN** calling `remove_tags("Tell me @memory query about this")`
- **THEN** returns "Tell me  about this"

#### Scenario: Extract only tag text

- **WHEN** calling `extract_tag_text("Hello @memory query world")`
- **THEN** returns "@memory query"

### Requirement: Normalize queries

The tag parser SHALL provide query normalization to improve matching consistency.

#### Scenario: Lowercase normalization

- **WHEN** normalizing query "Dark Keyboard"
- **THEN** returns "dark keyboard"

#### Scenario: Whitespace normalization

- **WHEN** normalizing query "query   with    spaces"
- **THEN** returns "query with spaces" (single spaces)

#### Scenario: Punctuation trimming

- **WHEN** normalizing query "query text..."
- **THEN** returns "query text" (trailing punctuation removed)

### Requirement: Support custom tags

The tag parser SHALL allow registration of custom tag patterns beyond the built-in @memory/@code/@session.

#### Scenario: Default tags only

- **WHEN** parser is initialized without custom tags
- **THEN** only recognizes @memory, @code, @session

#### Scenario: Register custom tag

- **WHEN** user registers '@docs' as valid tag
- **THEN** parser detects `@docs query` and returns ParsedTag

#### Scenario: Custom tag with modifier

- **WHEN** user input contains `@docs:api authentication`
- **THEN** parser returns ParsedTag with tag='@docs', modifier='api', query='authentication'
