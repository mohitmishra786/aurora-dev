# Tutorial 01: Hello World

Your first agent run.

**Last Updated:** February 8, 2026
**Difficulty:** Beginner
**Time:** 5 mins

## Goal

Create an agent that writes a Python script to print "Hello, Aurora!".

## Step 1: Initialize

```bash
mkdir hello-aurora
cd hello-aurora
aurora init --name hello-world
```

## Step 2: Define Task

Create `task.md`:
```markdown
# Objective
Write a python script called `hello.py` that prints "Hello, Aurora!".
```

## Step 3: Run

```bash
aurora run --task task.md
```

## Step 4: Verify

You should see a new file `hello.py`.
Run it:
```bash
python hello.py
# Output: Hello, Aurora!
```

## Next Step

[Tutorial 02: CRUD API](./tutorial_02_crud_api.md)
