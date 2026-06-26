# audience-card-tool

观众信息卡自动裁剪、分类、PPT 生成工具。

## MVP 目标

第一阶段先做一个本地网页工具，解决现场效率问题：

1. 批量上传总卡照片。
2. 每张总卡固定版式：横 9 列 × 竖 3 行，共 27 个卡槽。
3. 人工确认分类：男高 / 男富 / 男帅 / 女白 / 女富 / 女美。
4. 每张大总卡自动裁剪为两张小总卡：
   - 左图：4 列 × 3 行，共 12 个卡槽。
   - 右图：5 列 × 3 行，共 15 个卡槽。
5. 上传 PPT 模板。
6. 每页 PPT 放 1 张小总卡。
7. 按分类插入对应主题页，页数不足时自动复制模板页。
8. 导出新的 PPT 文件。

## 当前开发原则

- 先做稳定 MVP，不做全自动神仙识别。
- 不识别观众手写自评。
- 不根据文字内容去重，避免把相似答案误删。
- 裁剪前后卡槽数量必须一致。
- 分类先以人工确认为准，自动识别只做辅助。
- 真实观众照片不要提交到 GitHub。

## 建议运行方式

后端：Python FastAPI  
前端：React + Vite  
图像处理：OpenCV  
PPT 生成：python-pptx  
本地记录：JSON / SQLite，第一版先用 JSON。

## 快速启动（规划中）

```bash
# backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# frontend
cd frontend
npm install
npm run dev
```

打开前端页面后上传照片和 PPT 模板，人工确认分类，再生成 PPT。

## 重要提醒

仓库当前如果是 public，请不要上传真实观众信息卡照片。正式使用前建议改成 private。