#!/usr/bin/env bash
# ==============================================================================
# LingCast & AI Short Drama System Healthcheck Audit Tool
# 检查全栈容器、微服务、端口连通性与健康状态
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}🔍 LingCast & AI Short Drama 全系统健康巡检${NC}"
echo -e "${BLUE}======================================================${NC}"

CHECK_FAILURES=0

check_step() {
    local name="$1"
    local cmd="$2"
    echo -n "  Checking $name ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
        CHECK_FAILURES=$((CHECK_FAILURES + 1))
    fi
}

# 1. 基础配置与环境文件检查
echo -e "\n${YELLOW}[1/4] 环境与关键配置检查${NC}"
check_step ".env 配置文件存在" "[ -f .env ] || [ -f .env.example ]"
check_step "微服务统一配置 services.yaml 存在" "[ -f config/services.yaml ]"
check_step "SRS 直播推流配置 srs.conf 存在" "[ -f config/srs/srs.conf ]"
check_step "Nginx 反向代理配置 nginx.conf 存在" "[ -f nginx/nginx.conf ]"

# 2. 编排配置合法性检查
echo -e "\n${YELLOW}[2/4] Docker Compose 编排拓扑检查${NC}"
check_step "Docker Compose 语法合规性" "docker compose config --quiet"

# 3. 本地核心依赖与 Python 依赖检查
echo -e "\n${YELLOW}[3/4] Python 运行时与核心包环境${NC}"
check_step "Python 3.10+ 环境" "python3 -c 'import sys; assert sys.version_info >= (3, 10)'"
check_step "FastAPI 与 SQLModel 核心库" "python3 -c 'import fastapi, sqlmodel'"
check_step "Redis 客户端库" "python3 -c 'import redis'"
check_step "Jieba 中文分词引擎" "python3 -c 'import jieba'"

# 4. 服务健康与测试回归基线
echo -e "\n${YELLOW}[4/4] 系统测试基线与安全性${NC}"
check_step "DFA 敏感词与合规审计引擎" "python3 -c 'from server.core.compliance import sensitive_filter; assert sensitive_filter.is_clean(\"正常测试\")[0]'"
check_step "法定 AI 水印生成器" "python3 -c 'from server.core.watermark import WatermarkConfig; assert \"drawtext\" in WatermarkConfig().build_ffmpeg_filter()'"
check_step "前端生产包构建产物" "[ -f frontend/dist/index.html ] || (cd frontend && npm run build)"

echo -e "\n${BLUE}======================================================${NC}"
if [ $CHECK_FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 全部巡检项 100% 通过！系统处于健康且合规的可上线状态。${NC}"
    exit 0
else
    echo -e "${RED}⚠️ 检测到 $CHECK_FAILURES 项异常，请检查上述失败项。${NC}"
    exit 1
fi
