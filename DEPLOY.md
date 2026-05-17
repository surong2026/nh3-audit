# 部署指南

为让多位同事同时访问审核系统，提供两种部署方案。

## 方案一：Streamlit Cloud (推荐，免费)

### 步骤 1: 创建 GitHub 仓库

```bash
cd /home/sr200/workspace/nh3_audit

# 初始化 git
git init
git add .
git commit -m "氨氮分析记录审核系统 HJ 535-2009"

# 推送到 GitHub (先在你的 GitHub 上创建空仓库 nh3-audit)
git remote add origin https://github.com/你的用户名/nh3-audit.git
git push -u origin main
```

### 步骤 2: 在 Streamlit Cloud 部署

1. 打开 https://streamlit.io/cloud
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择仓库 → 分支 → 主文件 `app.py`
5. 点击 Deploy

部署完成后获得一个 URL，例如 `https://你的用户名-nh3-audit-app-xxxx.streamlit.app`，同事可直接打开使用。

### 步骤 3: 设置访问权限

Streamlit Cloud 支持两种模式：
- **Public**: 所有人可通过链接访问
- **Private**: 需登录 GitHub 且被授权 (Settings → Sharing)

---

## 方案二：PythonAnywhere ($5/月)

### 步骤 1: 上传项目到 PythonAnywhere

```bash
# 在本地打包
cd /home/sr200/workspace
tar czf nh3_audit.tar.gz nh3_audit/

# 在 PythonAnywhere 的 Files 页面上传 nh3_audit.tar.gz
# 然后在 PythonAnywhere Console 中解压:
tar xzf nh3_audit.tar.gz
```

### 步骤 2: 安装依赖

在 PythonAnywhere Bash Console 中：
```bash
pip3 install --user streamlit
```

### 步骤 3: 创建 Web App

1. PythonAnywhere → Web 标签 → "Add a new web app"
2. 选择 "Manual configuration" → Python 3.10
3. 编辑 WSGI configuration file，路径改为:
   ```
   /home/你的用户名/nh3_audit/pa_wsgi.py
   ```

### 步骤 4: 修改 pa_wsgi.py 中的用户名

将 `pa_wsgi.py` 第 14 行的 `your-username` 替换为你的 PythonAnywhere 用户名。

### 步骤 5 (付费用户): 设置 Always-on Task

1. PythonAnywhere → Tasks 标签
2. 创建 Always-on task:
   ```
   cd /home/你的用户名/nh3_audit && python3 start_streamlit.py
   ```

### 步骤 6: 访问

Web app URL: `https://你的用户名.pythonanywhere.com`

### 注意事项 (免费账号)

- 免费账号 WSGI 代理不支持 WebSocket，Streamlit 的部分交互功能受限
- 免费 Console 空闲一段时间会断开
- **建议付费 $5/月 + 启用 Always-on task** 以获得完整体验

---

## 参数自定义

部署前可在 `config.py` 中调整各标准阈值来适配实验室的具体质控要求。
