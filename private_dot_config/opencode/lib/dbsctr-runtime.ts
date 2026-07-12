export async function run(argv: string[], cwd: string) {
  const child = Bun.spawn(argv, { cwd, stdout: "pipe", stderr: "pipe" })
  const [stdout, stderr, exitCode] = await Promise.all([
    new Response(child.stdout).text(),
    new Response(child.stderr).text(),
    child.exited,
  ])
  if (exitCode !== 0) throw new Error(stderr.trim() || `${argv[0]} exited ${exitCode}`)
  return stdout.trim()
}

export async function cycleStatus(cwd: string) {
  return await run(["dbsctrctl", "status", "--json"], cwd)
}

export async function beginCycle(args: {
  cycleId: string
  context: string
  risk: "routine" | "elevated" | "critical"
  deliveryIntent: "local" | "merge" | "release" | "deploy"
  planPath: string
}, cwd: string, launch = false, env = process.env) {
  const output = await run([
    "dbsctrctl", "begin",
    "--cycle-id", args.cycleId,
    "--context", args.context,
    "--risk", args.risk,
    "--delivery-intent", args.deliveryIntent,
    "--plan", args.planPath,
  ], cwd)
  const handoff = JSON.parse(output)
  if (!launch || env.HERDR_ENV !== "1") return { ...handoff, herdr: "not_launched" }
  try {
    await run([
      "herdr", "agent", "start", "opencode",
      "--cwd", handoff.worktree,
      "--focus", "--", "opencode", handoff.worktree,
    ], cwd)
    return { ...handoff, herdr: "launched" }
  } catch (error) {
    return { ...handoff, herdr: `launch_failed: ${error}` }
  }
}
