# Case Study: React Migration

From jQuery to Next.js.

**Last Updated:** February 8, 2026
**Industry:** Media

## Challenge

"NewsDaily" had a 10-year-old site built with jQuery and PHP templates. It was slow (Lighthouse score: 20) and hard to maintain.

## Solution

1. **Frontend Agent:** Fed it screenshots of the old site and asked it to recreate components in React + Tailwind.
2. **Vision Analysis:** The agent used GPT-4o-V to verify pixel-perfect implementation.

## Results

- **Performance:** Lighthouse score jumped to 95.
- **SEO:** Organic traffic increased by 40% due to Next.js SSR.

## Key Learnings

- **Component Library:** Creating a design system (Atom design) first was essential. The agent was confused until we defined the `Button` and `Card` components explicitly.

## Related Reading

- [Frontend Agent](../03_agent_specifications/07_frontend_agent.md)
- [Performance Tuning](../06_developer_guides/performance_tuning.md)
