# Gemini Memory

这个文件被用作当前项目的记忆区。您可以在这里记录希望我在未来对话中注意到的项目规范、依赖情况或特定背景信息。

## 协作与提交流程 (Git Conventions)
本项目由 User、Claude 和 Gemini 共同协作。为了区分贡献来源并保持代码历史清晰，Gemini 必须遵守以下 Git 约定：
1. **自动提交**：Gemini 在完成一项代码修改、功能开发或 Bug 修复后，需要主动执行 `git add` 和 `git commit`。
2. **Commit 格式标注**：在 Git Commit Message 中，必须明确标注提交者是 Gemini。例如使用 `feat(gemini): ...`，`fix(gemini): ...` 或 `docs(gemini): ...` 的格式。
3. **流程规范**：提交前应通过 `git diff HEAD` 确认修改内容无误，保证每次提交是一个相对完整的功能或修复单元。
