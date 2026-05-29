# Specification: Provider Interface

## ADDED Requirements

### Requirement: Define IContextProvider interface

The system SHALL provide an abstract base class IContextProvider that all providers must implement.

#### Scenario: Interface has retrieve method

- **WHEN** implementing IContextProvider
- **THEN** must implement `retrieve(request: ContextRequest) -> List[ContextItem]`

#### Scenario: Interface has is_available method

- **WHEN** implementing IContextProvider
- **THEN** must implement `is_available() -> bool`

#### Scenario: Interface has name property

- **WHEN** implementing IContextProvider
- **THEN** must implement `name` property returning string

#### Scenario: Interface has source_type property

- **WHEN** implementing IContextProvider
- **THEN** must implement `source_type` property returning one of "memory", "codebase", "session", or custom

### Requirement: Accept ContextRequest parameter

Provider retrieve() method SHALL accept a ContextRequest object containing query parameters.

#### Scenario: ContextRequest has tag field

- **WHEN** retrieve() receives request
- **THEN** request.tag contains the tag string (e.g., "@memory")

#### Scenario: ContextRequest has query field

- **WHEN** retrieve() receives request
- **THEN** request.query contains the search query string

#### Scenario: ContextRequest has project field

- **WHEN** retrieve() receives request
- **THEN** request.project contains current project name

#### Scenario: ContextRequest has filtering parameters

- **WHEN** retrieve() receives request
- **THEN** request includes max_items and min_relevance for filtering

#### Scenario: ContextRequest has cross-project flag

- **WHEN** retrieve() receives request
- **THEN** request.include_cross_project indicates if cross-project search requested

### Requirement: Return list of ContextItem

Provider retrieve() method SHALL return a list of ContextItem objects.

#### Scenario: Return empty list for no matches

- **WHEN** query has no matching results
- **THEN** provider returns empty list (not None)

#### Scenario: Return multiple items

- **WHEN** query matches multiple results
- **THEN** provider returns list with all ContextItem objects

#### Scenario: Items sorted by relevance

- **WHEN** returning multiple items
- **THEN** items SHOULD be sorted by relevance_score descending (highest first)

### Requirement: Respect max_items limit

Provider retrieve() method SHALL respect the max_items parameter from ContextRequest.

#### Scenario: Limit results to max_items

- **WHEN** request.max_items is 10 and 50 matches found
- **THEN** provider returns top 10 items only

#### Scenario: Return fewer than max_items

- **WHEN** request.max_items is 10 but only 3 matches found
- **THEN** provider returns all 3 items

#### Scenario: Default max_items

- **WHEN** request.max_items is not specified
- **THEN** provider uses reasonable default (e.g., 10)

### Requirement: Filter by min_relevance

Provider retrieve() method SHALL filter results by minimum relevance score.

#### Scenario: Exclude low relevance items

- **WHEN** request.min_relevance is 0.70 and item scores 0.65
- **THEN** provider excludes item from results

#### Scenario: Include high relevance items

- **WHEN** request.min_relevance is 0.70 and item scores 0.85
- **THEN** provider includes item in results

#### Scenario: Exact threshold match

- **WHEN** request.min_relevance is 0.70 and item scores exactly 0.70
- **THEN** provider includes item in results

### Requirement: Implement project isolation

Provider SHALL respect project boundaries by default (unless include_cross_project is True).

#### Scenario: Single project results

- **WHEN** request.project is "DarkKeyboard" and include_cross_project is False
- **THEN** provider returns only items with project="DarkKeyboard"

#### Scenario: Cross-project search

- **WHEN** request.include_cross_project is True
- **THEN** provider returns items from all projects

#### Scenario: Invalid project name

- **WHEN** request.project does not exist
- **THEN** provider returns empty list (no error)

### Requirement: Populate ContextItem fields

Provider SHALL populate all required ContextItem fields correctly.

#### Scenario: Required fields populated

- **WHEN** creating ContextItem
- **THEN** provider sets content, source, project, metadata, relevance_score, timestamp

#### Scenario: Source type matches provider

- **WHEN** provider.source_type is "memory"
- **THEN** all returned ContextItem objects have source="memory"

#### Scenario: Optional fields

- **WHEN** ContextItem represents code
- **THEN** provider MAY populate file_path and line_range

#### Scenario: Relevance score range

- **WHEN** creating ContextItem
- **THEN** relevance_score MUST be between 0.0 and 1.0

### Requirement: Check availability before use

Provider SHALL implement is_available() to indicate readiness.

#### Scenario: Available provider

- **WHEN** provider dependencies are met (e.g., database exists)
- **THEN** is_available() returns True

#### Scenario: Unavailable provider

- **WHEN** provider dependencies are missing (e.g., database not found)
- **THEN** is_available() returns False

#### Scenario: Availability is cached

- **WHEN** is_available() is called multiple times
- **THEN** provider MAY cache result for performance

#### Scenario: Injector respects availability

- **WHEN** provider.is_available() returns False
- **THEN** ContextInjector skips this provider

### Requirement: Provide descriptive name

Provider SHALL return a human-readable name for logging and debugging.

#### Scenario: Name for logging

- **WHEN** accessing provider.name
- **THEN** returns descriptive string like "SQLite Memory Provider"

#### Scenario: Name is unique

- **WHEN** multiple providers are registered
- **THEN** each provider SHOULD have distinct name for debugging

### Requirement: Handle errors gracefully

Provider retrieve() method SHALL handle errors without raising exceptions to public API.

#### Scenario: Database connection error

- **WHEN** database connection fails during retrieve()
- **THEN** provider logs error internally and returns empty list

#### Scenario: Query timeout

- **WHEN** query takes too long and times out
- **THEN** provider returns partial results or empty list (no exception)

#### Scenario: Invalid query format

- **WHEN** query contains invalid characters or syntax
- **THEN** provider sanitizes or returns empty list (no exception)

### Requirement: Support custom metadata

Provider SHALL populate metadata dictionary with provider-specific information.

#### Scenario: Memory provider metadata

- **WHEN** memory provider returns decision item
- **THEN** metadata includes {"type": "decision", "rationale": "..."}

#### Scenario: Code provider metadata

- **WHEN** code provider returns function
- **THEN** metadata MAY include {"language": "python", "function_name": "parse"}

#### Scenario: Custom provider metadata

- **WHEN** custom provider returns item
- **THEN** metadata can contain any JSON-serializable data

### Requirement: Enable extensibility

The interface SHALL support custom providers without modifying core library.

#### Scenario: Custom tag registration

- **WHEN** user creates CustomProvider and registers with '@custom' tag
- **THEN** system recognizes and uses provider for @custom queries

#### Scenario: Override built-in tags

- **WHEN** user registers provider for '@memory' tag
- **THEN** user's provider overrides default behavior

#### Scenario: Multiple providers per tag

- **WHEN** multiple providers registered for same tag
- **THEN** last registered provider wins (dict behavior)
