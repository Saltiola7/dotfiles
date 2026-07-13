import { tool } from "@opencode-ai/plugin"
import { beginCycle, cycleStatus, lifecycleAudit } from "../lib/dbsctr-runtime"

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
