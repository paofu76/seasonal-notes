# 季节笔记

一个基于 Python + PySide6 的 macOS 本地桌面笔记应用。

## 功能

- 春、夏、秋、冬主题切换
- 笔记新建、编辑、保存、删除和收藏
- 文本搜索与日期筛选
- 日期选择器和一键重置
- 粗体、斜体、下划线
- 清单、表格、图片插入
- 本地 JSON 数据保存

## 运行

```bash
python3 -m pip install PySide6
python3 app.py
```

## 打包 macOS 应用

```bash
python3 -m pip install PyInstaller
python3 -m PyInstaller --windowed --name "季节笔记" --icon "季节笔记.icns" --clean -y app.py
```

生成的应用位于 `dist/季节笔记.app`。
