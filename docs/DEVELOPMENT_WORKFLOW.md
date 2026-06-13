# Development Workflow

## 分支规范

```
main          ← 主分支，只接受合并，不直接开发
feature/*    ← 功能开发分支
```

### 分支命名

- `feature/video-capability-lab-v0.1` - V0.1 架构骨架
- `feature/video-capability-lab-v0.1.1-ai-news-flow` - V0.1.1 AI 资讯流程深化
- `feature/video-capability-lab-v0.2-local-ffmpeg` - V0.2 本地 FFmpeg 真实 MP4

## 开发流程

### 1. 开始新任务

```bash
# 确保 main 是最新的
git checkout main
git pull origin main

# 从 main 切新功能分支
git checkout -b feature/xxx-description
```

### 2. 开发过程中

- 多次小提交，保持原子性
- 每次提交前跑测试
- 不要在 feature 分支上直接修改 docs/CHANGELOG.md 以外的文档

### 3. 完成任务

```bash
# 跑测试
python -m pytest tests/test_video_lab.py -v
python -m compileall app/ -q
cd frontend && npx tsc --noEmit

# 提交
git add .
git commit -m "feat: 描述"

# 推送（如果 remote 存在）
git push -u origin feature/xxx-description
```

### 4. 合并到 main

通过 PR 合并，不直接在 main 上开发。

## 提交规范

### Commit Message 格式

```
<type>: <short description>

<longer description if needed>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Type:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `test`: 测试
- `refactor`: 重构

### 禁止提交

- `.env` / 密钥文件
- `node_modules/`
- `dist/` / `build/` 产物
- 真实视频大文件
- `__pycache__/` / `.pyc`

## 测试规范

### 必须跑测试的情况

- 完成一个功能块后
- 提交前
- PR 合并前

### 测试命令

```bash
# 后端单元测试
python -m pytest tests/test_video_lab.py -v

# Python 编译检查
python -m compileall app/ -q

# 前端 TypeScript 检查
cd frontend && npx tsc --noEmit

# 前端构建
cd frontend && npm run build
```

## 文档同步

- README.md 随架构重大变化更新
- docs/ 目录下的文档随对应模块更新
- CHANGELOG.md 每轮任务完成后更新
- 文档变更和代码变更在同一 commit 或连续 commit

## 完成后汇报格式

```
1. 当前分支名：
2. main 分支是否存在：
3. 当前是否仍在 feature 分支开发：
4. base commit：
5. latest commit hash：
6. git status --short 是否干净：
7. remote 是否存在：
8. 是否 push 成功：
9. 新增/修改文件清单：
...（按任务要求）
```

## 任务完成标准

1. 所有测试通过
2. TypeScript 编译通过（如果有前端改动）
3. Python 编译通过
4. git status 干净
5. 文档已更新
6. 汇报已提交
