#!/usr/bin/env bash
# ==============================================================================
# GitHub 安全备份与状态同步脚本 (AI Short Drama Factory)
# 功能：
# 1. 自动扫描未忽略的敏感配置 (.env, *.key, *.db) 与大文件 (>50MB)
# 2. 检查本地与 GitHub 远端分支同步状态
# 3. 提供一键安全备份提交与推送流程 (优先推送私有 origin)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "========================================================"
echo "📦 AI Short Drama — GitHub 备份与安全审查工具"
echo "工作区路径: $REPO_DIR"
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 当前分支: $CURRENT_BRANCH"

# 1. 敏感配置预检
echo -e "\n🔍 [步骤 1/4] 扫描敏感文件与潜在凭证泄露..."
LEAK_FOUND=0
for sensitive_pattern in "\.env$" "\.env\.local$" "\.key$" "server/data/app\.db" "\.secret$"; do
    FOUND_FILES=$(git status --porcelain | awk '{print $2}' | grep -E "$sensitive_pattern" || true)
    if [ -n "$FOUND_FILES" ]; then
        echo "❌ 警告: 发现敏感文件处于未忽略/暂存状态: $FOUND_FILES"
        LEAK_FOUND=1
    fi
done

if [ $LEAK_FOUND -eq 1 ]; then
    echo "🚨 请先完善 .gitignore 并从暂存区撤出敏感文件，已中止备份！"
    exit 1
else
    echo "✅ 敏感文件安全排查通过（无敏感密钥/数据库待提交）。"
fi

# 2. 超大文件预检 (>50MB)
echo -e "\n🔍 [步骤 2/4] 检查是否有未忽略的大文件 (>50MB)..."
LARGE_FILES=$(find . -maxdepth 3 -type f -size +50M \
    -not -path "*/.git/*" \
    -not -path "*/out/*" \
    -not -path "*/projects/*" \
    -not -path "*/assets/models/*" \
    -not -path "*/node_modules/*" || true)

if [ -n "$LARGE_FILES" ]; then
    echo "⚠️ 发现大于 50MB 的未归档文件:"
    echo "$LARGE_FILES"
    echo "提示: 请确认这些大文件已在 .gitignore 中忽略，避免导致 GitHub push 失败。"
else
    echo "✅ 无异常大文件占用代码仓库空间。"
fi

# 3. 检查与远程的差异
echo -e "\n🔍 [步骤 3/4] 对比 GitHub 远程仓库状态..."
git fetch origin "$CURRENT_BRANCH" --quiet 2>/dev/null || true
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "origin/$CURRENT_BRANCH" 2>/dev/null || echo "NONE")

if [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then
    BEHIND_AHEAD="已完全对齐"
else
    AHEAD_COUNT=$(git rev-list --count "origin/$CURRENT_BRANCH..HEAD" 2>/dev/null || echo "0")
    BEHIND_COUNT=$(git rev-list --count "HEAD..origin/$CURRENT_BRANCH" 2>/dev/null || echo "0")
    BEHIND_AHEAD="领先远程 $AHEAD_COUNT 个 commit, 落后 $BEHIND_COUNT 个 commit"
fi
echo "远程仓库 (origin): $BEHIND_AHEAD"

# 4. 工作区改动汇总与交互确认
CHANGES_COUNT=$(git status --porcelain | wc -l | tr -d ' ')

if [ "$1" == "--status-only" ] || [ "$1" == "-s" ]; then
    echo -e "\n📊 当前有 $CHANGES_COUNT 处文件改动待提交。"
    git status -s
    echo -e "\n✅ 状态检查完毕 (--status-only)。"
    exit 0
fi

if [ "$CHANGES_COUNT" -eq 0 ] && [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then
    echo -e "\n🎉 本地工作区完全干净，且已与 GitHub 远程仓库完全同步，无需备份！"
    exit 0
fi

if [ "$CHANGES_COUNT" -gt 0 ]; then
    echo -e "\n📝 待备份的改动列表 ($CHANGES_COUNT 项):"
    git status -s
    
    COMMIT_MSG="${1:-chore(backup): snapshot workspace updates on $(date '+%Y-%m-%d %H:%M')}"
    echo -e "\n🚀 正在将改动暂存并提交 (commit message: '$COMMIT_MSG')..."
    git add .
    git commit -m "$COMMIT_MSG"
fi

echo -e "\n⬆️ [步骤 4/4] 推送至 GitHub (origin/$CURRENT_BRANCH)..."
git push origin "$CURRENT_BRANCH"

echo -e "\n========================================================"
echo "🎉 恭喜！GitHub 私有仓库备份同步成功！"
echo "远程仓库地址: https://github.com/cruise991/ai-short-drama/tree/$CURRENT_BRANCH"
echo "最新 Commit: $(git rev-parse --short HEAD) - $(git log -1 --pretty=%B | head -n 1)"
echo "========================================================"
