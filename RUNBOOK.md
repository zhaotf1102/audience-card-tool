# 本地运行手册

## 1. 克隆仓库

```bash
git clone https://github.com/zhaotf1102/audience-card-tool.git
cd audience-card-tool
```

## 2. 启动后端

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

如果 PowerShell 不允许激活虚拟环境，可临时执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：

```text
http://localhost:5173
```

## 4. MVP 使用流程

1. 点击创建项目。
2. 上传总卡照片。
3. 为每张照片确认分类。
4. 上传 PPT 模板。
5. 点击开始裁剪。
6. 检查裁剪预览。
7. 点击生成 PPT。
8. 下载生成的新 PPT。

## 5. 手机扫码上传规划

MVP 先使用电脑网页上传。后续可以把 Vite 或正式前端服务暴露在局域网，手机访问电脑 IP 上传。

示例：

```text
http://电脑局域网IP:5173
```

后端已经使用 `--host 0.0.0.0`，前端 dev 命令也配置了 `--host 0.0.0.0`。

## 6. 已知限制

- 当前裁剪默认把整张照片当作总卡区域。
- 如果照片含有大量背景、歪斜严重，需要后续加入透视校正。
- PPT 模板页码目前固定为第 1-6 页对应 6 个分类。
- 新页面目前追加到模板后面，暂不删除原模板页。
