#!/bin/bash

###############################################################################
# Trading AI - 自动安装脚本
# 功能：自动安装 Docker、Docker Compose，并部署 Trading AI 项目
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

# 检测是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_warning "检测到 root 用户，某些操作可能需要普通用户权限"
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        print_info "检测到操作系统: $OS $OS_VERSION"
    else
        print_error "无法检测操作系统类型"
        exit 1
    fi
}

# 检测 Docker 是否已安装
check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_success "Docker 已安装: $DOCKER_VERSION"
        return 0
    else
        print_warning "Docker 未安装"
        return 1
    fi
}

# 检测 Docker Compose 是否已安装
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_success "Docker Compose 已安装: $COMPOSE_VERSION"
        return 0
    elif docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version)
        print_success "Docker Compose (v2) 已安装: $COMPOSE_VERSION"
        USE_DOCKER_COMPOSE_V2=true
        return 0
    else
        print_warning "Docker Compose 未安装"
        return 1
    fi
}

# 安装 Docker（Ubuntu/Debian）
install_docker_ubuntu() {
    print_info "正在安装 Docker (Ubuntu/Debian)..."
    
    # 更新软件包索引
    sudo apt-get update
    
    # 安装依赖
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加 Docker 官方 GPG 密钥
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # 设置仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装 Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    print_success "Docker 安装完成"
}

# 安装 Docker（CentOS/RHEL/Fedora）
install_docker_centos() {
    print_info "正在安装 Docker (CentOS/RHEL/Fedora)..."
    
    # 安装依赖
    sudo yum install -y yum-utils
    
    # 添加 Docker 仓库
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # 安装 Docker
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # 启动 Docker 服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    print_success "Docker 安装完成"
}

# 安装 Docker（根据操作系统）
install_docker() {
    detect_os
    
    case $OS in
        ubuntu|debian)
            install_docker_ubuntu
            ;;
        centos|rhel|fedora)
            install_docker_centos
            ;;
        *)
            print_error "不支持的操作系统: $OS"
            print_info "请手动安装 Docker: https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
    
    # 添加当前用户到 docker 组（可选）
    if [ "$EUID" -ne 0 ]; then
        print_info "正在将当前用户添加到 docker 组..."
        sudo usermod -aG docker $USER
        print_warning "需要重新登录或运行 'newgrp docker' 才能使用 Docker（无需 sudo）"
    fi
}

# 安装 Docker Compose（独立版本，用于兼容旧版本）
install_docker_compose_standalone() {
    print_info "正在安装 Docker Compose..."
    
    # 下载最新版本
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose 安装完成"
}

# 交互式配置环境变量
configure_env() {
    print_header "配置环境变量"
    
    # 检查是否已存在 .env 文件
    if [ -f .env ]; then
        print_warning "检测到已存在的 .env 文件"
        read -p "是否要覆盖现有配置？(y/N): " overwrite
        if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
            print_info "跳过配置，使用现有 .env 文件"
            return 0
        fi
    fi
    
    # 从 env.example 复制
    if [ -f env.example ]; then
        cp env.example .env
        print_info "已从 env.example 创建 .env 文件"
    else
        print_error "未找到 env.example 文件"
        return 1
    fi
    
    echo ""
    print_info "开始交互式配置（直接按 Enter 使用默认值）"
    echo ""
    
    # Binance API 配置
    print_header "Binance API 配置"
    echo "从币安账户获取 API 密钥: https://www.binance.com/zh-CN/my/settings/api-management"
    echo "需要权限：读取、现货&杠杆交易（观察）、合约交易（观察）"
    echo ""
    
    read -p "Binance API Key: " api_key
    if [ ! -z "$api_key" ]; then
        sed -i "s|BINANCE_API_KEY=.*|BINANCE_API_KEY=$api_key|g" .env
    fi
    
    read -p "Binance API Secret: " api_secret
    if [ ! -z "$api_secret" ]; then
        sed -i "s|BINANCE_API_SECRET=.*|BINANCE_API_SECRET=$api_secret|g" .env
    fi
    
    # 交易环境
    print_header "交易环境配置"
    echo "observe: 观察模式（仅分析，不执行交易）"
    echo "testnet: 测试网模式（使用测试网执行交易）"
    echo "mainnet: 实盘模式（⚠️ 真实资金，请谨慎！）"
    read -p "交易环境 [observe/testnet/mainnet] (默认: observe): " trading_env
    if [ ! -z "$trading_env" ]; then
        sed -i "s|TRADING_ENVIRONMENT=.*|TRADING_ENVIRONMENT=$trading_env|g" .env
    fi
    
    # K线周期
    read -p "K线时间周期 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d) (默认: 15m): " timeframe
    if [ ! -z "$timeframe" ]; then
        sed -i "s|TIMEFRAME=.*|TIMEFRAME=$timeframe|g" .env
    fi
    
    # AI 配置
    print_header "AI 配置"
    echo "AI 提供商选项: deepseek, modelscope, openai, claude, gemini, mock"
    read -p "AI 提供商 (默认: mock): " ai_provider
    if [ ! -z "$ai_provider" ]; then
        sed -i "s|AI_PROVIDER=.*|AI_PROVIDER=$ai_provider|g" .env
    fi
    
    if [ "$ai_provider" != "mock" ] && [ ! -z "$ai_provider" ]; then
        read -p "AI API Key: " ai_api_key
        if [ ! -z "$ai_api_key" ]; then
            sed -i "s|AI_API_KEY=.*|AI_API_KEY=$ai_api_key|g" .env
        fi
        
        read -p "AI 模型名称 (可选，直接按 Enter 使用默认): " ai_model
        if [ ! -z "$ai_model" ]; then
            sed -i "s|AI_MODEL=.*|AI_MODEL=$ai_model|g" .env
        fi
    fi
    
    # 扫描配置
    print_header "扫描配置"
    read -p "扫描类型 [hot/volume/gainers/losers] (默认: hot,volume,gainers,losers): " scan_types
    if [ ! -z "$scan_types" ]; then
        sed -i "s|SCAN_TYPES=.*|SCAN_TYPES=$scan_types|g" .env
    fi
    
    read -p "扫描返回的交易对数量 (默认: 20): " scan_top_n
    if [ ! -z "$scan_top_n" ]; then
        sed -i "s|SCAN_TOP_N=.*|SCAN_TOP_N=$scan_top_n|g" .env
    fi
    
    read -p "是否启用自动循环扫描？(true/false) (默认: false): " auto_scan
    if [ ! -z "$auto_scan" ]; then
        sed -i "s|AUTO_SCAN=.*|AUTO_SCAN=$auto_scan|g" .env
    fi
    
    # 风险管理
    print_header "风险管理配置"
    read -p "账户余额 (USDT) (默认: 10000): " account_balance
    if [ ! -z "$account_balance" ]; then
        sed -i "s|ACCOUNT_BALANCE=.*|ACCOUNT_BALANCE=$account_balance|g" .env
    fi
    
    read -p "单笔交易风险百分比 (默认: 1.0): " risk_percent
    if [ ! -z "$risk_percent" ]; then
        sed -i "s|RISK_PERCENT=.*|RISK_PERCENT=$risk_percent|g" .env
    fi
    
    read -p "默认杠杆倍数 (默认: 10): " default_leverage
    if [ ! -z "$default_leverage" ]; then
        sed -i "s|DEFAULT_LEVERAGE=.*|DEFAULT_LEVERAGE=$default_leverage|g" .env
    fi
    
    print_success "环境变量配置完成"
    echo ""
    print_info "配置文件已保存到: $(pwd)/.env"
    print_info "你可以随时编辑此文件来修改配置"
}

# 检查项目文件
check_project() {
    if [ ! -f "main.py" ] || [ ! -f "docker-compose.yml" ] || [ ! -f "Dockerfile" ]; then
        print_error "当前目录不是 Trading AI 项目目录"
        print_info "请确保在项目根目录运行此脚本"
        exit 1
    fi
    print_success "项目文件检查通过"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p data logs
    print_success "目录创建完成"
}

# 构建 Docker 镜像
build_docker_image() {
    print_header "构建 Docker 镜像"
    
    if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
        docker compose build
    else
        docker-compose build
    fi
    
    print_success "Docker 镜像构建完成"
}

# 启动服务
start_service() {
    print_header "启动 Trading AI 服务"
    
    if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    print_success "服务已启动"
    echo ""
    print_info "查看日志: docker compose logs -f"
    print_info "停止服务: docker compose down"
    print_info "重启服务: docker compose restart"
}

# 显示状态
show_status() {
    print_header "服务状态"
    
    if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
        docker compose ps
    else
        docker-compose ps
    fi
    
    echo ""
    if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
        print_info "实时日志: docker compose logs -f trading-ai"
    else
        print_info "实时日志: docker-compose logs -f trading-ai"
    fi
}

# 主函数
main() {
    print_header "Trading AI - 自动安装脚本"
    
    # 检查 root
    check_root
    
    # 检查 Docker
    if ! check_docker; then
        print_header "安装 Docker"
        read -p "是否要安装 Docker？(Y/n): " install_docker_confirm
        if [ "$install_docker_confirm" != "n" ] && [ "$install_docker_confirm" != "N" ]; then
            install_docker
            print_warning "如果这是首次安装，请重新运行此脚本或运行 'newgrp docker'"
            exit 0
        else
            print_error "Docker 未安装，无法继续"
            exit 1
        fi
    fi
    
    # 检查 Docker Compose
    if ! check_docker_compose; then
        # Docker Compose v2 通常与 Docker 一起安装
        # 如果没有，尝试安装独立版本
        print_header "安装 Docker Compose"
        read -p "是否要安装 Docker Compose？(Y/n): " install_compose_confirm
        if [ "$install_compose_confirm" != "n" ] && [ "$install_compose_confirm" != "N" ]; then
            install_docker_compose_standalone
        else
            print_error "Docker Compose 未安装，无法继续"
            exit 1
        fi
    fi
    
    # 检查项目
    check_project
    
    # 创建目录
    create_directories
    
    # 配置环境变量
    configure_env
    
    # 构建镜像
    read -p "是否要立即构建 Docker 镜像并启动服务？(Y/n): " build_confirm
    if [ "$build_confirm" != "n" ] && [ "$build_confirm" != "N" ]; then
        build_docker_image
        start_service
        show_status
    else
        print_info "跳过构建，你可以稍后运行："
        if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
            echo "  docker compose build"
            echo "  docker compose up -d"
        else
            echo "  docker-compose build"
            echo "  docker-compose up -d"
        fi
    fi
    
    print_success "安装脚本执行完成！"
}

# 运行主函数
main

