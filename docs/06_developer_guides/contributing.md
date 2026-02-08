# Contributing

Join the revolution.

**Last Updated:** February 8, 2026
**Audience:** Everyone

> **Before Reading This**
>
> You should understand:
> - [Development Setup](./development_setup.md)
> - [Code of Conduct](../20_community/community_resources.md)

## Types of Contributions

We welcome more than just code.

1. **Bug Reports:** Found a crash? Hallucination? Open an Issue.
2. **Documentation:** Fix typos, add examples, translate guides.
3. **Plugins:** Build a new Agent or Tool and publish it.
4. **Core Code:** Fix internal logic or add features.

## The Pull Request Lifecycle

1. **Triage:** A maintainer reviews the issue.
2. **Implementation:** You write the code.
3. **Review:** The `Code Reviewer Agent` (and a human) checks your code.
4. **Merge:** Your code is merged to `main`.
5. **Release:** It goes out in the next SemVer tag.

## Style Guide

- **Python:** Black formatter, Google-style docstrings.
- **TypeScript:** Prettier, ESLint.
- **Commits:** Conventional Commits (`feat: add login`, `fix: typo`).

## Testing Policy

If you add code, you *must* add tests.
- **Unit Tests:** For logic functions.
- **Integration Tests:** For database/API interactions.
- **E2E Tests:** For critical user flows.

Code coverage must remain above 85%.

## Legal

You must sign the CLA (Contributor License Agreement) before we can merge your code. This ensures we can keep the project open source forever.

## Related Reading

- [Development Setup](./development_setup.md)
- [Coding Standards](./coding_standards.md)
