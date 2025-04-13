#!/usr/bin/env node

const spawn = require('cross-spawn');
const path = require('path');
const fs = require('fs');

// 检查Python是否已安装
function checkPython() {
  console.log('正在检查Python环境...');
  
  try {
    const result = spawn.sync('python', ['-c', 'import sys; print(sys.version)'], { 
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'] 
    });
    
    if (result.status === 0) {
      console.log(`Python已安装: ${result.stdout.trim()}`);
      return true;
    } else {
      console.error('Python未安装或无法正常运行');
      console.error('请安装Python 3.6或更高版本');
      return false;
    }
  } catch (error) {
    console.error('检查Python失败:', error.message);
    return false;
  }
}

// 安装依赖
function installDependencies() {
  console.log('正在安装依赖...');
  
  const requirementsPath = path.join(__dirname, 'requirements.txt');
  
  if (!fs.existsSync(requirementsPath)) {
    console.error('缺少requirements.txt文件');
    return false;
  }
  
  try {
    const installProcess = spawn.sync('pip', ['install', '-r', requirementsPath], {
      encoding: 'utf8',
      stdio: 'inherit'
    });
    
    if (installProcess.status === 0) {
      console.log('依赖安装成功');
      return true;
    } else {
      console.error('依赖安装失败');
      return false;
    }
  } catch (error) {
    console.error('安装依赖时出错:', error.message);
    return false;
  }
}

// 创建必要的目录
function createDirectories() {
  console.log('正在创建必要的目录...');
  
  const directories = ['ts_files', 'output'];
  
  directories.forEach(dir => {
    if (!fs.existsSync(dir)) {
      try {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`创建目录: ${dir}`);
      } catch (error) {
        console.error(`创建目录 ${dir} 失败:`, error.message);
      }
    } else {
      console.log(`目录已存在: ${dir}`);
    }
  });
  
  return true;
}

// 启动MCP服务器
function startMcpServer() {
  console.log('正在启动MCP服务器...');
  
  const serverPath = path.join(__dirname, 'mcp_server.py');
  
  if (!fs.existsSync(serverPath)) {
    console.error('未找到mcp_server.py文件');
    return false;
  }
  
  try {
    // 关键修复：使用stdio: 'inherit' 让Python进程直接与Cursor通信
    // 这样所有的输入输出流都会直接传递给父进程
    const serverProcess = spawn('python', [serverPath], {
      stdio: 'inherit',
      detached: false
    });
    
    // 处理进程终止
    serverProcess.on('error', (error) => {
      console.error(`MCP服务器启动错误: ${error.message}`);
    });
    
    // 注意：不要在这里立即退出Node.js进程
    // 让Python进程接管标准输入输出
    
    return true;
  } catch (error) {
    console.error('启动MCP服务器失败:', error.message);
    return false;
  }
}

// 主函数
function main() {
  console.log('欢迎使用MCP M3U8下载器');
  
  if (!checkPython() || !installDependencies() || !createDirectories()) {
    console.error('初始化失败，程序退出');
    process.exit(1);
  }
  
  startMcpServer();
  
  // 不要在这里退出Node.js进程
  // 服务器需要继续运行并等待Python进程结束
}

main(); 