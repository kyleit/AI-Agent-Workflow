# AIWF Runtime Analytics Roadmap

## Phase 1 – Context Breakdown
Goal: Show exactly where the current context is consumed.
- Breakdown by Conversation, Prompt, AI_RULES, SKILL, Blueprint, Memory, RAG, Workspace, Tool Results, Logs.
- Percentage per source.
- Collapsible tree.
**Success:** Identify largest context contributor in under 10 seconds.

## Phase 2 – Request History
Goal: Audit every provider request.
- Timeline
- Input/Output/Cache/Thinking
- Cost
- Duration
- Skill
- Model
- Tool count
**Success:** Every request is independently traceable.

## Phase 3 – Token Diff Analysis
Goal: Explain why context changes.
- Previous vs Current request
- Added/Removed tokens
- Largest delta contributors
**Success:** Users know exactly what increased context.

## Phase 4 – Runtime Insights
Goal: Detect runtime inefficiencies.
- Top token consumers
- Repeated AI_RULES/SKILL/Blueprint loads
- Workspace scan statistics
- Memory/RAG hit ratio
**Success:** Optimization opportunities are immediately visible.

## Phase 5 – Optimization Advisor
Goal: Recommend concrete improvements.
- Optimization score
- Estimated token savings
- Estimated cost savings
- Ranked recommendations
**Success:** Actionable recommendations replace raw metrics.

## Phase 6 – Context Timeline
Goal: Correlate workflow events with context growth.
- Timeline
- Skill markers
- Context spikes
- Cost growth
**Success:** Users understand when context exploded.

## Phase 7 – Context Budget Controller
Goal: Prevent context explosion.
- Thresholds
- Predictive growth
- Budget policies
- Suggestions (Resume, Refresh Memory, Sub-agent)
**Success:** Reduce accumulated input by at least 50%.

## Phase 8 – Smart Context Rebuilder
Goal: Rebuild minimal context instead of replaying history.
- Stateless requests
- Hash-based cache
- Symbol cache
- Incremental loading
- Context deduplication
**Success:** Reduce accumulated provider input by 80–95%.

## Priority
1. Context Breakdown
2. Request History
3. Token Diff
4. Runtime Insights
5. Optimization Advisor
6. Context Timeline
7. Context Budget Controller
8. Smart Context Rebuilder
