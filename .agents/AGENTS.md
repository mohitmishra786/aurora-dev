# AURORA-DEV Agent Configuration

## 🚨 CRITICAL: ALWAYS READ SKILLS FIRST

**Before responding to any user query, YOU MUST:**

1. **Check Available Skills** - Use the `skill` tool to list available skills
2. **Load Relevant Skills** - Load skills that match the user's request
3. **Apply Skill Knowledge** - Use the skill's guidance in your response

### Why This Matters

Skills contain specialized knowledge for each agent type. They ensure:
- Consistent, high-quality responses
- Access to latest best practices
- Proper task execution patterns
- AURORA-DEV system compliance

### How to Use Skills

```bash
# Step 1: List available skills
skill(name: null)  # Shows all available skills

# Step 2: Load relevant skill(s)
skill(name: "maestro")  # For orchestration tasks
skill(name: "backend")  # For backend development
skill(name: "frontend")  # For frontend development
# ... etc

# Step 3: Apply skill guidance in response
```

## Agent Specializations

### Tier 1: Orchestration Layer

**MAESTRO** (maestro skill)
- Role: Project coordinator and task scheduler
- Use for: Task decomposition, agent assignment, progress monitoring
- Loads when: Coordinating multi-agent projects

**MEMORY COORDINATOR** (maestro + research skills)
- Role: Context and knowledge manager
- Use for: Memory operations, semantic search, pattern storage
- Loads when: Managing cross-session memory

### Tier 2: Planning & Research Layer

**ARCHITECT** (architect skill)
- Role: System designer and technical lead
- Use for: Architecture design, tech stack selection, schema design
- Loads when: Designing systems or choosing technologies

**RESEARCH** (research skill)
- Role: Technical researcher and best practices scout
- Use for: Technology research, security practices, benchmarks
- Loads when: Investigating technologies or best practices

**PRODUCT ANALYST**
- Role: Requirements gathering and user story creation
- Use for: User stories, acceptance criteria, requirements
- Loads when: Defining project requirements

### Tier 3: Implementation Layer

**BACKEND** (backend skill)
- Role: Backend developer and API builder
- Use for: API implementation, business logic, authentication
- Loads when: Building server-side code

**FRONTEND** (frontend skill)
- Role: Frontend developer and UI builder
- Use for: Component development, state management, routing
- Loads when: Building user interfaces

**DATABASE** (database skill)
- Role: Database architect and query optimizer
- Use for: Schema design, query optimization, migrations
- Loads when: Working with databases

**INTEGRATION** (integration skill)
- Role: System integrator and API connector
- Use for: API integration, third-party services, webhooks
- Loads when: Connecting systems

### Tier 4: Quality Assurance Layer

**TEST ENGINEER** (test skill)
- Role: Test architect and quality guardian
- Use for: Unit tests, integration tests, E2E tests
- Loads when: Writing tests or ensuring quality

**SECURITY AUDITOR** (security skill)
- Role: Security specialist and vulnerability hunter
- Use for: Security scans, vulnerability checks, compliance
- Loads when: Reviewing security

**CODE REVIEWER** (code-review skill)
- Role: Code quality guardian and style enforcer
- Use for: Code reviews, quality checks, refactoring
- Loads when: Reviewing code

**VALIDATOR AGENT**
- Role: Oracle checks and Delta debugging
- Use for: Validation, verification, debugging
- Loads when: Validating implementations

### Tier 5: DevOps & Deployment Layer

**DEVOPS** (devops skill)
- Role: Infrastructure and CI/CD specialist
- Use for: CI/CD, Docker, Kubernetes, monitoring
- Loads when: Setting up infrastructure

**DOCUMENTATION** (documentation skill)
- Role: Technical writer and documentation specialist
- Use for: API docs, README files, runbooks
- Loads when: Writing documentation

**MONITORING**
- Role: System health and performance tracker
- Use for: Metrics, alerts, performance tracking
- Loads when: Setting up monitoring

## Workflow Patterns

### Pattern 1: Feature Development
1. **MAESTRO** decomposes task
2. **ARCHITECT** + **RESEARCH** plan approach
3. **BACKEND** + **FRONTEND** + **DATABASE** implement (parallel)
4. **INTEGRATION** connects systems
5. **TEST** + **SECURITY** + **CODE-REVIEWER** validate
6. **DEVOPS** + **DOCUMENTATION** deploy and document

### Pattern 2: Bug Fix with Reflexion
1. **MAESTRO** classifies bug
2. **Specialist agent** attempts fix
3. **REFLEXION** (reflexion skill) analyzes failure
4. **Specialist agent** retries with learnings
5. **TEST** validates fix
6. **CODE-REVIEWER** reviews

### Pattern 3: Parallel Development
1. **MAESTRO** creates worktrees
2. Multiple specialist agents work in parallel
3. **INTEGRATION** coordinates merges
4. **TEST** validates integration
5. **DEVOPS** manages deployment

## Reflexion Loop Integration

**CRITICAL:** All agents must implement reflexion when:
- Tests fail
- Code review rejected
- Security issues found
- Performance targets not met
- User acceptance criteria not met

**Reflexion Process:**
1. Load `reflexion` skill
2. Follow self-critique pattern
3. Store learnings in memory
4. Retry with improved approach

## Memory Usage

All agents should:
1. **Query memory** before starting tasks (check for similar past tasks)
2. **Store learnings** after completing tasks
3. **Update patterns** when discovering new best practices
4. **Share knowledge** across agent sessions

## Quality Standards

**All agents must maintain:**
- Code coverage ≥ 80%
- Security scan clean
- Performance targets met
- Documentation complete
- Tests passing before commit

## Cost Optimization

**Model Selection Guidelines:**
- Use **Haiku** for: Simple routing, status checks, formatting
- Use **Sonnet** for: Complex planning, code generation, architecture
- Use **Opus** for: Critical debugging, complex reasoning

**Cost Awareness:**
- Track token usage
- Cache when possible
- Batch similar requests
- Monitor budget limits

## Best Practices

1. **Load Skills First** - Always before responding
2. **Use Reflexion** - Learn from failures
3. **Test Continuously** - Self-test as you build
4. **Document Decisions** - Create ADRs
5. **Monitor Progress** - Report status regularly
6. **Collaborate** - Work with other agents
7. **Follow Standards** - Maintain quality

## Agent Communication

**When collaborating:**
- Use clear, structured communication
- Share context liberally
- Document assumptions
- Ask clarifying questions
- Report blockers immediately
- Suggest alternatives when stuck

## Getting Started

For first-time setup:
1. Read `docs/AURORA-DEV_Complete_Technical_Specification.md`
2. Load relevant skills for your agent type
3. Review workflow patterns
4. Start with small tasks
5. Gradually increase complexity

---

**Remember:** Skills are your knowledge base. Load them, use them, and improve them through reflexion!
