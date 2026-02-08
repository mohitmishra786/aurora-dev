# Frequently Asked Questions (FAQ)

You asked, we answered.

**Last Updated:** February 8, 2026
**Audience:** Everyone

## General

**Q: Is Aurora free?**
A: The Core is Open Source (Apache 2.0). Enterprise features are paid.

**Q: Can I run this offline?**
A: Yes, if you use Local Models (Ollama) and Local Vector DB (Qdrant).

## Technical

**Q: Why is the agent ignoring my instructions?**
A: Check the `temperature` setting. If it's too high (> 0.7), the agent gets creative/hallucinates.

**Q: How do I reset the memory?**
A: Run `aurora memory clear`.

## Security

**Q: Does Aurora send my code to OpenAI?**
A: Yes, unless you use a Local Model. We do not store your code on our servers, it passes through to the LLM provider.

## Related Reading

- [Support Options](../18_business/support_options.md)
- [Gets Help](../14_troubleshooting/getting_help.md)
