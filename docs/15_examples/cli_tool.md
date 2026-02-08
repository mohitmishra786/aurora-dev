# Example: CLI Tool

Building command-line tools with AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Prompt

```markdown
Build a CLI tool for managing AWS resources.

Features:
- List EC2 instances
- Start/stop instances
- View CloudWatch metrics
- Cost reporting
- Interactive and scripting modes
- Config file support

Tech: Python, Click, Rich
```

## Generated Structure

```
aws-cli/
├── aws_manager/
│   ├── __main__.py
│   ├── cli.py
│   ├── commands/
│   │   ├── ec2.py
│   │   └── costs.py
│   └── utils/
└── tests/
```

## Usage

```bash
aws-manager ec2 list
aws-manager ec2 start i-123456
aws-manager costs --monthly
```

## Related Reading

- [Project Types](../05_user_guides/project_types.md)
