export HEIMDALLR_MANAGER_MODEL="gpt-4o"
export HEIMDALLR_AUDITOR_MODEL="claude-3-opus-20240229" # 示例，需确保您的 base_url 支持
export HEIMDALLR_CHECKER_MODEL="gemini-1.5-pro-latest"
# 或者都使用 gemini-2.0-flash
# export HEIMDALLR_MANAGER_MODEL="gemini-2.0-flash"
# export HEIMDALLR_AUDITOR_MODEL="gemini-2.0-flash"
# export HEIMDALLR_CHECKER_MODEL="gemini-2.0-flash"

# 2.  **命令行参数**:
# ... existing code ...
--manager-model "gemini-1.5-flash-latest" \
--auditor-model "gemini-1.5-flash-latest" \
--checker-model "gemini-1.5-pro-latest"
# 或者使用 gemini-2.0-flash
# python -m heimdallr.main --file examples/sample_code_to_audit.py --auditor-model "gemini-2.0-flash"

## 输出
# ... existing code ...

注意：上述模型名称是示例，请使用您的 API Provider 支持的实际模型 ID。 