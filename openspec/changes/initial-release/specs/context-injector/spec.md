# Specification: Context Injector

## ADDED Requirements

### Requirement: Initialize with configuration

The ContextInjector SHALL accept configuration during initialization.

#### Scenario: Initialize with providers

- **WHEN** creating ContextInjector with providers dictionary
- **THEN** injector registers all provided providers by tag

#### Scenario: Initialize with project name

- **WHEN** creating ContextInjector with project="DarkKeyboard"
- **THEN** injector uses "DarkKeyboard" as current project

#### Scenario: Initialize with defaults

- **WHEN** creating ContextInjector with default_max_items and default_min_relevance
- **THEN** injector uses these defaults for all queries

#### Scenario: Initialize without project

- **WHEN** creating ContextInjector with project=None
- **THEN** injector auto-detects project from current working directory

### Requirement: Parse user input for tags

The ContextInjector SHALL use TagParser to detect and parse tags from user input.

#### Scenario: Input with single tag

- **WHEN** inject() called with "@memory keyboard layout"
- **THEN** injector parses tag and extracts query

#### Scenario: Input with multiple tags

- **WHEN** inject() called with "@memory query1 and @code query2"
- **THEN** injector processes both tags

#### Scenario: Input without tags

- **WHEN** inject() called with plain text
- **THEN** injector returns None (no context injection needed)

### Requirement: Route tags to providers

The ContextInjector SHALL route each tag to its registered provider.

#### Scenario: Route @memory to memory provider

- **WHEN** tag is "@memory" and memory provider is registered
- **THEN** injector calls memory provider's retrieve() method

#### Scenario: Route @code to code provider

- **WHEN** tag is "@code" and code provider is registered
- **THEN** injector calls code provider's retrieve() method

#### Scenario: Unregistered tag

- **WHEN** tag is "@unknown" and no provider registered
- **THEN** injector skips tag and logs warning

#### Scenario: Multiple tags to same provider

- **WHEN** input has two "@memory" tags
- **THEN** injector calls memory provider twice with different queries

### Requirement: Handle cross-project modifier

The ContextInjector SHALL detect `:all` modifier and enable cross-project search.

#### Scenario: Tag with :all modifier

- **WHEN** tag is "@memory:all query"
- **THEN** injector sets include_cross_project=True in ContextRequest

#### Scenario: Tag without modifier

- **WHEN** tag is "@memory query"
- **THEN** injector sets include_cross_project=False in ContextRequest

#### Scenario: Cross-project with unavailable provider

- **WHEN** tag is "@memory:all" but provider is unavailable
- **THEN** injector returns None gracefully

### Requirement: Create ContextRequest objects

The ContextInjector SHALL construct proper ContextRequest objects for each provider call.

#### Scenario: Request includes tag

- **WHEN** constructing request for "@memory query"
- **THEN** request.tag is "@memory"

#### Scenario: Request includes query

- **WHEN** constructing request for "@memory keyboard layout"
- **THEN** request.query is "keyboard layout"

#### Scenario: Request includes project

- **WHEN** current project is "DarkKeyboard"
- **THEN** request.project is "DarkKeyboard"

#### Scenario: Request includes limits

- **WHEN** default_max_items is 10 and default_min_relevance is 0.70
- **THEN** request includes these values

### Requirement: Aggregate results from multiple tags

The ContextInjector SHALL combine results from all parsed tags.

#### Scenario: Combine results from two tags

- **WHEN** "@memory query1" returns 3 items and "@code query2" returns 2 items
- **THEN** injector aggregates all 5 items

#### Scenario: Empty results from one tag

- **WHEN** "@memory query" returns 0 items and "@code query" returns 5 items
- **THEN** injector returns 5 items total

#### Scenario: All tags return empty

- **WHEN** all providers return empty lists
- **THEN** injector returns None

### Requirement: Deduplicate context items

The ContextInjector SHALL remove duplicate items from aggregated results.

#### Scenario: Duplicate by content

- **WHEN** two tags return items with identical first 100 characters
- **THEN** injector keeps only one copy

#### Scenario: Similar but not identical

- **WHEN** two items differ in content
- **THEN** injector keeps both items

#### Scenario: Cross-provider duplicates

- **WHEN** memory and code providers return same content
- **THEN** injector deduplicates across providers

### Requirement: Sort results by relevance

The ContextInjector SHALL sort aggregated results by relevance score.

#### Scenario: Sort descending

- **WHEN** items have scores [0.75, 0.90, 0.65]
- **THEN** final order is [0.90, 0.75, 0.65]

#### Scenario: Maintain sort after deduplication

- **WHEN** deduplication removes items
- **THEN** remaining items stay sorted by relevance

### Requirement: Limit total items

The ContextInjector SHALL apply max_items limit to final aggregated results.

#### Scenario: Limit aggregated results

- **WHEN** max_items is 10 and aggregation produces 25 items
- **THEN** injector keeps top 10 by relevance

#### Scenario: Fewer items than limit

- **WHEN** max_items is 10 but only 5 items found
- **THEN** injector returns all 5 items

### Requirement: Format context for injection

The ContextInjector SHALL use ContextFormatter to format final output.

#### Scenario: Format with delimiters

- **WHEN** items are ready for output
- **THEN** injector uses formatter to add BEGIN/END delimiters

#### Scenario: Include anti-hallucination rules

- **WHEN** formatting with default settings
- **THEN** output includes anti-hallucination rules

#### Scenario: Detect cross-project results

- **WHEN** results include items from different projects
- **THEN** formatter adds cross-project warning

### Requirement: Return formatted string

The inject() method SHALL return formatted context string or None.

#### Scenario: Return formatted context

- **WHEN** tags found and context retrieved
- **THEN** inject() returns formatted string ready for LLM prompt

#### Scenario: Return None for no tags

- **WHEN** input has no valid tags
- **THEN** inject() returns None

#### Scenario: Return None for no results

- **WHEN** tags found but all providers return empty
- **THEN** inject() returns None

### Requirement: Provide metrics via inject_with_metrics()

The ContextInjector SHALL provide a method that returns full ContextResponse with metrics.

#### Scenario: Response includes performance metrics

- **WHEN** calling inject_with_metrics()
- **THEN** response includes performance_ms timing

#### Scenario: Response includes counts

- **WHEN** calling inject_with_metrics()
- **THEN** response includes total_found and filtered_count

#### Scenario: Response includes items

- **WHEN** calling inject_with_metrics()
- **THEN** response includes original ContextItem list

### Requirement: Check provider availability

The ContextInjector SHALL verify provider availability before calling retrieve().

#### Scenario: Skip unavailable providers

- **WHEN** provider.is_available() returns False
- **THEN** injector skips that provider and logs warning

#### Scenario: Use available providers only

- **WHEN** 2 of 3 providers are available
- **THEN** injector uses only the 2 available providers

#### Scenario: All providers unavailable

- **WHEN** all providers return is_available()=False
- **THEN** inject() returns None

### Requirement: Handle provider errors

The ContextInjector SHALL handle provider errors gracefully without crashing.

#### Scenario: Provider raises exception

- **WHEN** provider.retrieve() raises exception
- **THEN** injector catches error, logs warning, continues with other providers

#### Scenario: Partial results on error

- **WHEN** one of two providers fails
- **THEN** injector returns results from successful provider

#### Scenario: All providers fail

- **WHEN** all providers raise exceptions
- **THEN** inject() returns None

### Requirement: Support has_tags() utility

The ContextInjector SHALL provide utility method to check for tags without processing.

#### Scenario: Has tags returns True

- **WHEN** calling has_tags("@memory query")
- **THEN** returns True

#### Scenario: Has tags returns False

- **WHEN** calling has_tags("plain text")
- **THEN** returns False

### Requirement: Support extract_query_only() utility

The ContextInjector SHALL provide utility to remove tags from input.

#### Scenario: Remove single tag

- **WHEN** calling extract_query_only("Tell me @memory query about this")
- **THEN** returns "Tell me  about this"

#### Scenario: Remove multiple tags

- **WHEN** calling extract_query_only("@memory query1 and @code query2")
- **THEN** returns remainder after tags removed

### Requirement: Auto-detect project from cwd

The ContextInjector SHALL auto-detect current project when not explicitly provided.

#### Scenario: Detect from known path

- **WHEN** cwd is "/home/user/Project/my-app" and project map includes this path
- **THEN** injector sets project to mapped name

#### Scenario: Detect from directory name

- **WHEN** cwd is "/home/user/unknown-project" and not in project map
- **THEN** injector uses directory name "unknown-project"

#### Scenario: Explicit project overrides detection

- **WHEN** initialized with explicit project="CustomProject"
- **THEN** injector uses "CustomProject" regardless of cwd

### Requirement: Support custom project mapping

The ContextInjector SHALL allow users to provide custom project path mappings.

#### Scenario: Provide custom mapping

- **WHEN** initialized with project_paths dictionary
- **THEN** injector uses custom mapping for auto-detection

#### Scenario: Default mapping

- **WHEN** initialized without project_paths
- **THEN** injector uses directory name fallback

### Requirement: Maintain performance target

The ContextInjector SHALL complete typical queries in under 25ms.

#### Scenario: Single tag query performance

- **WHEN** injecting context with one @memory tag
- **THEN** total time (parse + retrieve + format) is <25ms median

#### Scenario: Multiple tag query performance

- **WHEN** injecting context with three tags
- **THEN** total time is <50ms median

#### Scenario: Performance monitoring

- **WHEN** using inject_with_metrics()
- **THEN** performance_ms field reports actual timing

### Requirement: Thread safety

The ContextInjector SHALL be thread-safe for concurrent inject() calls.

#### Scenario: Concurrent inject calls

- **WHEN** multiple threads call inject() simultaneously
- **THEN** each call completes correctly without data corruption

#### Scenario: Provider thread safety

- **WHEN** provider is shared across threads
- **THEN** provider is responsible for its own thread safety
