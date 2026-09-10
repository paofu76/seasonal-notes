# 季节笔记

一个基于 Python + PySide6 的 macOS 本地桌面笔记应用。

## 功能

- 春、夏、秋、冬主题切换
- 四季独立 3D 渲染场景：城市花房、海岛露台、艺术校园、城市雪夜
- 图片网格局部变形模拟花枝、树叶和纱帘随风摆动，配合水面波动、飘落花瓣与分层雪景（图片驱动，非实时 3D）
- 动态氛围支持手动关闭和窗口失焦自动暂停
- 笔记新建、编辑、保存、删除和收藏
- 文本搜索与日期筛选
- 日期选择器和一键重置
- 粗体、斜体、下划线
- 清单、表格、图片插入
- 本地 JSON 数据保存

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m seasonal_notes
```

## 打包 macOS 应用

```bash
python -m PyInstaller --clean -y 季节笔记.spec
```

生成的应用位于 `dist/季节笔记.app`。

## 工程结构

```text
app.py                         兼容启动入口
seasonal_notes/
  application.py               Qt 应用生命周期
  storage.py                   存储、首次迁移和原子写入（不依赖 Qt）
  themes.py                    四季配色配置
  assets/seasons-3d-atlas.png   四季场景素材，随安装包与桌面应用分发
  ui/
    main_window.py             主窗口、对话框与笔记操作
    note_item.py               笔记摘要列表组件
    editor.py                  富文本编辑器
    table_preview.py           表格预览
    animations.py              四季动画与胶囊
    wind_scene.py              局部风动、水面与天气渲染
tests/                         隔离存储测试
.github/workflows/tests.yml    GitHub 自动检查
pyproject.toml                 安装入口、依赖和开发工具配置
seasonal-notes.entitlements   App Sandbox 权限模板
```

## Mac App Store 准备

应用已配置 Bundle ID `com.paofu.seasonalnotes`、生产力分类、版本号、高分辨率支持和沙盒权限模板。提交商店前仍需在拥有 Apple Developer 证书的电脑上完成 Developer ID / App Store 签名、沙盒签名、归档、公证或 Transporter 上传，并补齐商店截图、隐私政策和应用描述。

## 验证与开发约定

```sh
python -m unittest discover -s tests -v
ruff check seasonal_notes tests
python -m compileall -q seasonal_notes
```

依赖以 `pyproject.toml` 为准。PyCharm 使用 `.venv` 解释器，运行模块 `seasonal_notes`。保留 `python app.py` 和安装后的 `seasonal-notes` 启动方式。

数据在 `~/Library/Application Support/季节笔记/`，开发测试用 `SEASONAL_NOTES_DATA_DIR` 指向临时目录。首次迁移不覆盖已有数据，损坏数据不会静默当作空列表。构建不包含个人笔记或附件。

测试目前覆盖存储迁移、损坏文件和持久化，不代表完整 GUI 验收。新增功能将持久化逻辑放在 `storage.py`、界面放在 `ui/`，并增加对应验证。主窗口仍包含日期和表格对话框，后续可随功能迭代进一步拆分。不要提交个人笔记、附件、密钥、虚拟环境和打包产物。
