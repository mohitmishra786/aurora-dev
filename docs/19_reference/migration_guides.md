# Migration Guides

Moving up in the world.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Upgrade Guide](../08_deployment/upgrade_guide.md)
> - [Changelog](./changelog.md)

## v1.x -> v2.0

**Breaking Changes:**
- `aurora.config.json` is now `aurora.yaml`.
- The `search_tool` has been renamed to `web_search`.

**Steps:**
1. Run `aurora migrate config`.
2. Update your agent definitions to use the new tool names.

## v2.0 -> v2.1

**New Features:**
- Added `Anthropic` support.
- Added `Vector Memory`.

**Steps:**
1. Run `aurora db upgrade`.
2. Set `OPENAI_API_KEY` (if not already set).

## Related Reading

- [Changelog](./changelog.md)
- [Upgrade Guide](../08_deployment/upgrade_guide.md)
