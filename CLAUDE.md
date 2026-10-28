# CLAUDE.md

このリポジトリの指示は AGENTS.md にまとめてある（Codex と共通）。

@AGENTS.md

Claude Code だけの補足：
- 独立レビューは `.claude/agents/video-reviewer.md` のサブエージェントでもよい。渡すのは `qc/<版>/review_pack/`（`bash scripts/45_review_pack.sh <版>`）。
- HyperFrames のスキルの既定の見た目より docs/04 を優先する。
