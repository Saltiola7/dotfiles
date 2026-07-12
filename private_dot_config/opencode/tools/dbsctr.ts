import { tool } from "@opencode-ai/plugin"
import { beginCycle, cycleStatus } from "../lib/dbsctr-runtime"

export const status = tool({
  description: "Read authoritative DBSCTR cycle status for the current worktree.",
  args: {},
  async execute(_args, context) {
    return await cycleStatus(context.worktree)
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
    return JSON.stringify(await beginCycle(args, context.worktree, args.launch))
  },
})
