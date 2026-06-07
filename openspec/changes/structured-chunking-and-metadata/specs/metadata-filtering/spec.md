## ADDED Requirements

### Requirement: Attach arbitrary metadata to documents
The system SHALL accept arbitrary JSON metadata when indexing documents.

#### Scenario: Metadata is stored with document
- **WHEN** user calls `index(content, metadata={"os": "linux", "difficulty": "medium"})`
- **THEN** metadata is stored and retrievable with search results

#### Scenario: Metadata is optional
- **WHEN** user calls `index(content)` without metadata
- **THEN** document is indexed with empty metadata `{}`

#### Scenario: Metadata is merged with auto-generated fields
- **WHEN** user provides `metadata={"os": "linux"}`
- **THEN** final metadata includes user fields plus auto-generated fields like `{"os": "linux", "chunking_strategy": "by_size", "indexed_at": "2026-06-07T..."}`

### Requirement: Filter search results by metadata
The system SHALL filter search results based on metadata criteria.

#### Scenario: Exact match filtering
- **WHEN** user calls `search(query, filters={"os": "linux"})`
- **THEN** only results where `metadata["os"] == "linux"` are returned

#### Scenario: Multiple filter criteria (AND logic)
- **WHEN** user calls `search(query, filters={"os": "linux", "difficulty": "medium"})`
- **THEN** only results matching ALL criteria are returned

#### Scenario: Filter on nested metadata
- **WHEN** user calls `search(query, filters={"tags.category": "web"})`
- **THEN** results where `metadata["tags"]["category"] == "web"` are returned

#### Scenario: No filters returns all results
- **WHEN** user calls `search(query)` without filters
- **THEN** all semantically matching results are returned regardless of metadata

### Requirement: Metadata filtering happens after semantic search
The system SHALL apply metadata filters to semantic search results, not before embedding lookup.

#### Scenario: Filtering reduces result set
- **WHEN** semantic search returns 100 results and filters match 20
- **THEN** final result set contains 20 items

#### Scenario: Empty result set when no matches
- **WHEN** semantic search returns results but none match filters
- **THEN** empty result set is returned with message "No results match filters"

### Requirement: Metadata validation is user responsibility
The system SHALL NOT validate metadata schema - users provide any valid JSON.

#### Scenario: Any JSON structure is accepted
- **WHEN** user provides `metadata={"custom_field": [1, 2, 3], "nested": {"a": "b"}}`
- **THEN** metadata is stored as-is without validation

#### Scenario: Invalid JSON is rejected
- **WHEN** user provides non-JSON-serializable metadata
- **THEN** system raises `ValueError` with message "Metadata must be JSON-serializable"
