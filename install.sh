#!/bin/bash

###############################################################################
# Trading AI - 管理脚本
# 功能：自动安装 Docker、配置环境、管理服务
###############################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
}

print_menu_header() {
    clear
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║           🤖 Trading AI - 管理菜单                        ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检测 Docker Compose 命令
get_compose_cmd() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
        USE_DOCKER_COMPOSE_V2=true
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
        USE_DOCKER_COMPOSE_V2=false
    else
        echo ""
        return 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        OS="unknown"
    fi
}

# 检测 Docker 是否已安装
check_docker() {
    if command -v docker &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# 检测 Docker Compose 是否已安装
check_docker_compose() {
    if [ ! -z "$COMPOSE_CMD" ]; then
        return 0
    else
        return 1
    fi
}

# 安装 Docker（Ubuntu/Debian）
install_docker_ubuntu() {
    print_info "正在安装 Docker (Ubuntu/Debian)..."
    
    sudo apt-get update -qq
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release > /dev/null 2>&1
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update -qq
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
    
    if [ "$EUID" -ne 0 ]; then
        sudo usermod -aG docker $USER 2>/dev/null
    fi
    
    print_success "Docker 安装完成"
    print_warning "如果这是首次安装，可能需要重新登录或运行 'newgrp docker'"
    sleep 2
}

# 安装 Docker（CentOS/RHEL/Fedora）
install_docker_centos() {
    print_info "正在安装 Docker (CentOS/RHEL/Fedora)..."
    
    sudo yum install -y yum-utils > /dev/null 2>&1
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo > /dev/null 2>&1
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
    
    sudo systemctl start docker
    sudo systemctl enable docker > /dev/null 2>&1
    
    if [ "$EUID" -ne 0 ]; then
        sudo usermod -aG docker $USER 2>/dev/null
    fi
    
    print_success "Docker 安装完成"
    print_warning "如果这是首次安装，可能需要重新登录或运行 'newgrp docker'"
    sleep 2
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
            read -p "按 Enter 继续..."
            return 1
            ;;
    esac
}

# 安装 Docker Compose（独立版本，用于兼容旧系统）
install_docker_compose_standalone() {
    print_info "正在安装 Docker Compose..."
    
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    
    sudo chmod +x /usr/local/bin/docker-compose
    COMPOSE_CMD="docker-compose"
    USE_DOCKER_COMPOSE_V2=false
    
    print_success "Docker Compose 安装完成"
    sleep 1
}

# 安装 Docker 和 Docker Compose（合并功能）
install_docker_and_compose() {
    print_header "安装 Docker 和 Docker Compose"
    
    # 检查 Docker
    docker_installed=false
    if check_docker; then
        print_info "Docker 已安装"
        docker_installed=true
    else
        print_info "正在安装 Docker..."
        install_docker
        if [ $? -eq 0 ]; then
            docker_installed=true
        else
            print_error "Docker 安装失败"
            read -p "按 Enter 继续..."
            return 1
        fi
    fi
    
    # 更新 COMPOSE_CMD（Docker 安装后可能需要重新检测）
    COMPOSE_CMD=$(get_compose_cmd)
    
    # 检查 Docker Compose
    if check_docker_compose; then
        print_info "Docker Compose 已安装"
    else
        print_info "正在安装 Docker Compose..."
        # Docker Compose v2 通常随 Docker 一起安装，如果没有则安装独立版本
        install_docker_compose_standalone
    fi
    
    # 最终检测
    COMPOSE_CMD=$(get_compose_cmd)
    if ! check_docker || ! check_docker_compose; then
        print_error "安装未完全成功，请检查错误信息"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    print_success "Docker 和 Docker Compose 安装完成！"
    
    if ! $docker_installed && [ "$EUID" -ne 0 ]; then
        print_warning "如果这是首次安装 Docker，可能需要重新登录或运行 'newgrp docker'"
    fi
    
    read -p "按 Enter 继续..."
}

# 交互式配置环境变量
configure_env() {
    print_header "配置环境变量"
    
    if [ ! -f env.example ]; then
        print_error "未找到 env.example 文件"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    if [ -f .env ]; then
        print_warning "检测到已存在的 .env 文件"
        read -p "是否要覆盖现有配置？(y/N): " overwrite
        if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
            print_info "跳过配置，使用现有 .env 文件"
            read -p "按 Enter 继续..."
            return 0
        fi
    fi
    
    cp env.example .env
    print_info "已从 env.example 创建 .env 文件"
    echo ""
    print_info "开始交互式配置（直接按 Enter 使用默认值）"
    echo ""
    
    # Binance API 配置
    print_header "Binance API 配置"
    echo "从币安账户获取: https://www.binance.com/zh-CN/my/settings/api-management"
    echo "需要权限：读取、现货&杠杆交易（观察）、合约交易（观察）"
    echo ""
    
    read -p "Binance API Key: " api_key
    if [ ! -z "$api_key" ]; then
        sed -i "s|BINANCE_API_KEY=.*|BINANCE_API_KEY=$api_key|g" .env
    fi
    
    read -sp "Binance API Secret: " api_secret
    echo ""
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
    read -p "K线时间周期 (默认: 15m): " timeframe
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
    read -p "扫描类型 (默认: hot,volume,gainers,losers): " scan_types
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
    print_info "配置文件已保存到: $(pwd)/.env"
    read -p "按 Enter 继续..."
}

# 检查项目文件
check_project() {
    if [ ! -f "main.py" ] || [ ! -f "docker-compose.yml" ] || [ ! -f "Dockerfile" ]; then
        return 1
    fi
    return 0
}

# 检查是否为 Git 仓库
check_git_repo() {
    if [ -d ".git" ]; then
        return 0
    else
        return 1
    fi
}

# 获取 GitHub 仓库 URL
get_repo_url() {
    if check_git_repo; then
        git remote get-url origin 2>/dev/null || echo "https://github.com/rdone4425/trading-ai.git"
    else
        echo "https://github.com/rdone4425/trading-ai.git"
    fi
}

# 下载/更新项目（合并功能）
download_or_update_project() {
    REPO_URL="https://github.com/rdone4425/trading-ai.git"
    
    # 如果项目存在且是 Git 仓库，执行更新
    if check_project && check_git_repo; then
        print_header "更新项目代码"
        
        print_info "正在检查更新..."
        
        # 获取当前分支
        current_branch=$(git branch --show-current 2>/dev/null || echo "main")
        print_info "当前分支: $current_branch"
        
        # 检查是否有未提交的更改
        if [ -n "$(git status -s)" ]; then
            print_warning "检测到未提交的更改"
            read -p "是否要先提交或暂存更改？(y/N): " handle_changes
            
            if [ "$handle_changes" = "y" ] || [ "$handle_changes" = "Y" ]; then
                print_info "你可以："
                echo "  1. git add . && git commit -m '你的提交信息'"
                echo "  2. git stash（暂存更改）"
                echo ""
                read -p "处理完成后按 Enter 继续更新..."
            else
                print_warning "未提交的更改可能会被覆盖"
                read -p "是否继续更新？(y/N): " continue_update
                if [ "$continue_update" != "y" ] && [ "$continue_update" != "Y" ]; then
                    return 0
                fi
            fi
        fi
        
        # 获取远程更新
        print_info "正在从 GitHub 拉取最新代码..."
        git fetch origin
        
        # 检查是否有更新
        local_hash=$(git rev-parse HEAD)
        remote_hash=$(git rev-parse origin/$current_branch 2>/dev/null)
        
        if [ "$local_hash" = "$remote_hash" ] || [ -z "$remote_hash" ]; then
            print_success "代码已是最新版本"
            read -p "按 Enter 继续..."
            return 0
        fi
        
        print_info "发现新版本，正在更新..."
        
        # 暂存当前更改（如果有）
        git stash > /dev/null 2>&1
        
        # 拉取更新
        git pull origin $current_branch
        
        if [ $? -eq 0 ]; then
            print_success "代码更新成功"
            
            # 恢复暂存的更改（如果有）
            if [ -n "$(git stash list)" ]; then
                print_info "检测到暂存的更改，正在恢复..."
                git stash pop > /dev/null 2>&1 || true
            fi
            
            # 检查是否需要重新构建
            if [ ! -z "$COMPOSE_CMD" ]; then
                print_info "检测到代码更新，需要重新构建镜像"
                read -p "是否立即重新构建并重启服务？(Y/n): " rebuild
                
                if [ "$rebuild" != "n" ] && [ "$rebuild" != "N" ]; then
                    # 检查服务是否运行
                    if $COMPOSE_CMD ps | grep -q "trading-ai.*Up"; then
                        print_info "服务正在运行，先停止服务..."
                        $COMPOSE_CMD down
                    fi
                    
                    # 重新构建
                    print_info "正在重新构建镜像..."
                    $COMPOSE_CMD build
                    
                    if [ $? -eq 0 ]; then
                        print_success "镜像构建完成"
                        
                        # 启动服务
                        read -p "是否立即启动服务？(Y/n): " start_now
                        if [ "$start_now" != "n" ] && [ "$start_now" != "N" ]; then
                            print_info "正在启动服务..."
                            $COMPOSE_CMD up -d
                            print_success "服务已启动"
                            sleep 1
                            show_status
                        fi
                    else
                        print_error "镜像构建失败"
                    fi
                fi
            fi
            
            read -p "按 Enter 继续..."
        else
            print_error "更新失败，请检查网络连接或 Git 配置"
            read -p "按 Enter 继续..."
            return 1
        fi
    
    # 如果项目不存在，执行下载
    elif ! check_project; then
        print_header "下载 Trading AI 项目"
        
        print_info "当前目录不是 Trading AI 项目"
        read -p "是否要在当前目录克隆项目？(Y/n): " clone_here
        
        if [ "$clone_here" != "n" ] && [ "$clone_here" != "N" ]; then
            if [ "$(ls -A . 2>/dev/null)" ]; then
                print_warning "当前目录不为空"
                read -p "是否继续？可能会覆盖现有文件 (y/N): " confirm
                if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
                    return 1
                fi
            fi
            
            print_info "正在克隆项目..."
            git clone "$REPO_URL" .
            
            if [ $? -eq 0 ]; then
                print_success "项目已克隆"
                # 赋予脚本执行权限
                chmod +x install.sh
                read -p "按 Enter 继续..."
                return 0
            else
                print_error "克隆失败"
                read -p "按 Enter 继续..."
                return 1
            fi
        else
            # 询问目标目录
            read -p "请输入目标目录路径: " target_dir
            if [ -z "$target_dir" ]; then
                print_error "目录路径不能为空"
                read -p "按 Enter 继续..."
                return 1
            fi
            
            if [ -d "$target_dir" ]; then
                print_error "目标目录已存在: $target_dir"
                read -p "按 Enter 继续..."
                return 1
            fi
            
            print_info "正在克隆到: $target_dir"
            git clone "$REPO_URL" "$target_dir"
            
            if [ $? -eq 0 ]; then
                print_success "项目已克隆到: $target_dir"
                print_info "请进入该目录运行: cd $target_dir && ./install.sh"
                read -p "按 Enter 继续..."
            else
                print_error "克隆失败"
                read -p "按 Enter 继续..."
                return 1
            fi
        fi
    
    # 项目存在但不是 Git 仓库
    else
        print_header "更新项目代码"
        print_error "当前目录不是 Git 仓库"
        print_info "无法更新，请手动初始化 Git 仓库或重新克隆项目"
        read -p "按 Enter 继续..."
        return 1
    fi
}

# 保留旧函数以向后兼容（已废弃，都调用合并函数）
download_project() {
    download_or_update_project
}

update_project() {
    download_or_update_project
}

# 创建必要的目录
create_directories() {
    mkdir -p data logs
}

# 构建 Docker 镜像
build_docker_image() {
    print_header "构建 Docker 镜像"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose 未安装"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    $COMPOSE_CMD build
    print_success "Docker 镜像构建完成"
    read -p "按 Enter 继续..."
}

# 启动服务
start_service() {
    print_header "启动 Trading AI 服务"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose 未安装"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    if [ ! -f .env ]; then
        print_warning "未找到 .env 文件，请先配置环境变量"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    create_directories
    $COMPOSE_CMD up -d
    
    print_success "服务已启动"
    read -p "按 Enter 继续..."
}

# 停止服务
stop_service() {
    print_header "停止 Trading AI 服务"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose 未安装"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    $COMPOSE_CMD down
    print_success "服务已停止"
    read -p "按 Enter 继续..."
}

# 重启服务
restart_service() {
    print_header "重启 Trading AI 服务"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose 未安装"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    $COMPOSE_CMD restart
    print_success "服务已重启"
    read -p "按 Enter 继续..."
}

# 查看日志
view_logs() {
    print_header "查看日志"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose 未安装"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    print_info "按 Ctrl+C 退出日志查看"
    sleep 2
    $COMPOSE_CMD logs -f trading-ai
}

# 查看状态
show_status() {
    print_header "服务状态"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose 未安装"
        read -p "按 Enter 继续..."
        return 1
    fi
    
    $COMPOSE_CMD ps
    echo ""
    print_info "实时日志: $COMPOSE_CMD logs -f trading-ai"
    read -p "按 Enter 继续..."
}

# 清理/卸载
cleanup() {
    print_header "清理/卸载"
    
    print_warning "此操作将："
    echo "  - 停止并删除容器"
    echo "  - 删除 Docker 镜像（可选）"
    echo "  - 清理数据目录（可选）"
    echo ""
    read -p "是否继续？(y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        return 0
    fi
    
    if [ ! -z "$COMPOSE_CMD" ]; then
        $COMPOSE_CMD down
        print_success "容器已删除"
        
        read -p "是否删除 Docker 镜像？(y/N): " delete_image
        if [ "$delete_image" = "y" ] || [ "$delete_image" = "Y" ]; then
            docker rmi trading-ai-trading-ai 2>/dev/null || true
            print_success "镜像已删除"
        fi
    fi
    
    read -p "是否清理数据目录（data/, logs/）？(y/N): " delete_data
    if [ "$delete_data" = "y" ] || [ "$delete_data" = "Y" ]; then
        rm -rf data/* logs/* 2>/dev/null || true
        print_success "数据目录已清理"
    fi
    
    read -p "按 Enter 继续..."
}

# 显示主菜单
show_menu() {
    print_menu_header
    
    # 检查 Docker 状态
    if check_docker; then
        DOCKER_STATUS="${GREEN}✓${NC}"
    else
        DOCKER_STATUS="${RED}✗${NC}"
    fi
    
    # 检查 Docker Compose 状态
    if check_docker_compose; then
        COMPOSE_STATUS="${GREEN}✓${NC}"
    else
        COMPOSE_STATUS="${RED}✗${NC}"
    fi
    
    # 检查项目状态
    GIT_STATUS=""
    UPDATE_STATUS=""
    if check_project; then
        PROJECT_STATUS="${GREEN}✓${NC}"
        if check_git_repo; then
            GIT_STATUS="${GREEN}✓${NC}"
            # 检查是否有更新
            git fetch origin > /dev/null 2>&1
            current_branch=$(git branch --show-current 2>/dev/null || echo "main")
            local_hash=$(git rev-parse HEAD 2>/dev/null)
            remote_hash=$(git rev-parse origin/$current_branch 2>/dev/null)
            if [ "$local_hash" != "$remote_hash" ] && [ ! -z "$remote_hash" ]; then
                UPDATE_STATUS="${YELLOW}有新版本${NC}"
            else
                UPDATE_STATUS="${GREEN}已最新${NC}"
            fi
        else
            GIT_STATUS="${RED}✗${NC}"
            UPDATE_STATUS="${RED}未知${NC}"
        fi
    else
        PROJECT_STATUS="${RED}✗${NC}"
        GIT_STATUS="${RED}✗${NC}"
        UPDATE_STATUS="${RED}未知${NC}"
    fi
    
    # 检查服务状态
    if [ ! -z "$COMPOSE_CMD" ]; then
        if $COMPOSE_CMD ps | grep -q "trading-ai.*Up"; then
            SERVICE_STATUS="${GREEN}运行中${NC}"
        else
            SERVICE_STATUS="${YELLOW}已停止${NC}"
        fi
    else
        SERVICE_STATUS="${RED}未知${NC}"
    fi
    
    echo -e "系统状态："
    echo -e "  Docker:        $DOCKER_STATUS"
    echo -e "  Docker Compose: $COMPOSE_STATUS"
    echo -e "  项目文件:      $PROJECT_STATUS"
    if [ ! -z "$GIT_STATUS" ]; then
        echo -e "  Git 仓库:      $GIT_STATUS"
        echo -e "  代码版本:      $UPDATE_STATUS"
    fi
    echo -e "  服务状态:      $SERVICE_STATUS"
    echo ""
    echo -e "${CYAN}请选择操作：${NC}"
    echo ""
    echo -e "${GREEN}项目管理：${NC}"
    echo "  [U] 下载/更新项目（自动检测：不存在则下载，存在则更新）"
    echo ""
    echo -e "${GREEN}环境准备：${NC}"
    echo "  [1] 安装 Docker 和 Docker Compose（自动检测并安装缺失组件）"
    echo "  [2] 配置环境变量"
    echo ""
    echo -e "${GREEN}服务管理：${NC}"
    echo "  [3] 构建 Docker 镜像"
    echo "  [4] 启动服务"
    echo "  [5] 停止服务"
    echo "  [6] 重启服务"
    echo "  [7] 查看日志"
    echo "  [8] 查看状态"
    echo ""
    echo -e "${GREEN}其他：${NC}"
    echo "  [C] 清理/卸载"
    echo "  [0] 退出"
    echo ""
    echo -ne "${YELLOW}请输入选项: ${NC}"
}

# 主循环
main() {
    # 如果不在项目目录，提示下载
    if ! check_project; then
        print_error "当前目录不是 Trading AI 项目目录"
        echo ""
        print_info "你可以："
        echo "  1. 在项目目录运行此脚本"
        echo "  2. 使用选项 [U] 下载项目到当前目录"
        echo ""
        read -p "是否现在下载项目？(Y/n): " download_now
        
        if [ "$download_now" != "n" ] && [ "$download_now" != "N" ]; then
            download_or_update_project
            # 重新检查
            if ! check_project; then
                print_error "项目下载失败或未完成，退出脚本"
                exit 1
            fi
        else
            print_info "退出脚本"
            exit 0
        fi
    fi
    
    # 更新 COMPOSE_CMD
    COMPOSE_CMD=$(get_compose_cmd)
    
    while true; do
        show_menu
        read choice
        
        case $choice in
            u|U)
                download_or_update_project
                # 如果下载成功，重新检查项目
                if check_project; then
                    COMPOSE_CMD=$(get_compose_cmd)
                fi
                ;;
            d|D)
                # 向后兼容：也支持 D 选项
                download_or_update_project
                if check_project; then
                    COMPOSE_CMD=$(get_compose_cmd)
                fi
                ;;
            1)
                install_docker_and_compose
                COMPOSE_CMD=$(get_compose_cmd)
                ;;
            2)
                configure_env
                ;;
            3)
                build_docker_image
                ;;
            4)
                start_service
                ;;
            5)
                stop_service
                ;;
            6)
                restart_service
                ;;
            7)
                view_logs
                ;;
            8)
                show_status
                ;;
            c|C)
                cleanup
                ;;
            0)
                print_info "退出脚本"
                exit 0
                ;;
            *)
                print_error "无效选项，请重新选择"
                sleep 1
                ;;
        esac
    done
}

# 运行主函数
main
