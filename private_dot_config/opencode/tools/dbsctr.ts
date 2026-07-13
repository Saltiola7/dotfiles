import { tool } from "@opencode-ai/plugin"
import { beginCycle, cycleStatus, fixedCommitInspect, lifecycleAudit } from "../lib/dbsctr-runtime"

export const status = tool({
  description: "Read authoritative DBSCTR cycle status for the current worktree.",
  args: {},
  async execute(_args, context) {
    return await cycleStatus(context.worktree)
  },
})

export const audit = tool({
  description: "Inventory DBSCTR lifecycle artifacts at a fixed Git commit without changing files.",
  args: { commit: tool.schema.string().optional().default("HEAD") },
  async execute(args, context) {
    return await lifecycleAudit(context.worktree, args.commit)
  },
})

export const inspect = tool({
  description: "Read, list, search, or inspect metadata from one fixed Git commit without using the worktree overlay.",
  args: {
    action: tool.schema.enum(["read", "tree", "search", "object"]),
    commit: tool.schema.string().optional().default("HEAD"),
    path: tool.schema.string().optional(),
    query: tool.schema.string().optional(),
    limit: tool.schema.number().int().optional(),
    offset: tool.schema.number().int().optional(),
    cursor: tool.schema.number().int().optional(),
    excerpt: tool.schema.number().int().optional(),
  },
  async execute(args, context) {
    return await fixedCommitInspect(args, context.worktree)
  },
})

export const begin = tool({
  description: "Create an isolated DBSCTR branch/worktree and optionally launch OpenCode there through Herdr.",
  args: {
    cycleId: tool.schema.string(),
    context: tool.schema.string(),
    risk: tool.schema.enum(["routine", "elevated", "critical"]),
    deliveryIntent: tool.schema.enum(["local", "merge", "release", "deploy"]),
    planPath: tool.schema.string(),
    launch: tool.schema.boolean().optional().default(false),
  },
  async execute(args, context) {
    await context.ask({
      permission: "dbsctr_begin",
      patterns: ["*"],
      always: [],
      metadata: {
        cycleId: args.cycleId,
        context: args.context,
        risk: args.risk,
        deliveryIntent: args.deliveryIntent,
      },
    })
    return JSON.stringify(await beginCycle(args, context.worktree, args.launch))
  },
})
