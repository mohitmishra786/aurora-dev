# Tutorial 07: Custom Agent

Building your own bot.

**Last Updated:** February 8, 2026
**Difficulty:** Advanced
**Time:** 30 mins

## Goal

Create a "Joke Agent" that only tells jokes.

## Step 1: Define Class

Create `agents/joke_agent.py`:
```python
class JokeAgent(BaseAgent):
    SYSTEM_PROMPT = "You are a comedian. Answer everything with a joke."
```

## Step 2: Register

Update `aurora.yaml`:
```yaml
agents:
  joker:
    class: agents.joke_agent.JokeAgent
```

## Step 3: Run

```bash
aurora run --task "Explain Quantum Physics" --agent joker
```

## Next Step

[Tutorial 08: Integration](./tutorial_08_integration.md)
