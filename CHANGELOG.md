# Changelog

All notable changes to FinSight are documented here.

## [Unreleased]

### Added

- Process-local TTL caching for upstream ticker and news requests.
- Retry with exponential backoff for upstream market and news providers.
- Configurable upstream timeout, cache and rate-limit settings.
- Explicit `data_status` metadata for analytics, fundamentals and news responses.
- URL-shareable stock searches with loading skeletons and sticky data tables.
- Repository structure and dashboard demo screenshots in the README.

### Improved

- Metric calculations preserve unavailable inputs instead of silently using zero.
- Provider access is isolated behind a replaceable market-data provider boundary.
- CORS origins and request limits are configurable through environment variables.

## [0.1.0]

- Initial FinSight research dashboard and comparison workflow.
