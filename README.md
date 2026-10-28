# 视频字幕翻译技能

将实际视频字幕处理经验整理成可分享的轻量 Agent Skill：**本地提取 → 当前助手翻译校对 → 字幕排版 → 本地压制 → 成片核验**。

English: A lightweight agent skill for extracting video subtitles, transcribing speech or recognizing on-screen text, translating with the current assistant, and producing verified Chinese subtitles or subtitled videos.

## 下载

- [最新发布与技能 ZIP](https://github.com/yan450863-ui/video-subtitle-translate/releases/latest)
- [直接下载 v1.0.1](https://github.com/yan450863-ui/video-subtitle-translate/releases/download/v1.0.1/video-subtitle-translate-v1.0.1.zip)
- [技能入口](skills/video-subtitle-translate/SKILL.md)

这是流程技能，不是独立桌面软件。包内不带 FFmpeg、Python 环境、字体、模型权重、视频或私人任务记录。

## 能做什么

- 优先提取可用文字字幕；没有字幕时按需选择语音识别或画面文字 OCR。
- 支持英文/日文等原文，由使用者当前的助手分批翻译；不依赖本地大语言翻译模型。
- 覆盖硬字幕、气泡文字、旁白及按任务要求处理的歌词。
- 思源黑体、白字黑描边、无黑底，对白默认底部居中；支持按画面调整位置。
- 保存提取、翻译和完成范围，避免中断后从头处理。
- 提供 Python 标准库脚本，核对 cue ID/时间轴并导出 SRT、ASS。
- 规定成片轨道/参数核对、完整解码、改名对照和原文件保护流程。

## 安装

### 用 Codex 技能安装器

将下面这句话交给具备技能安装能力的 Codex：

```text
使用 $skill-installer，从 https://github.com/yan450863-ui/video-subtitle-translate 安装 skills/video-subtitle-translate 目录中的技能。
```

### 手动安装

1. 下载 Release 中的 `video-subtitle-translate-v1.0.1.zip` 并解压。
2. 将完整的 `video-subtitle-translate` 文件夹放入客户端的技能目录。当前 Codex 官方文档列出的个人目录是 `~/.agents/skills/`，项目目录是 `.agents/skills/`；旧版或自定义安装器可能使用 `~/.codex/skills/`，以实际客户端配置为准。
3. 确认客户端能发现技能；未出现时重新加载或重启。

[Codex 官方技能说明](https://learn.chatgpt.com/docs/build-skills)。其他支持 SKILL.md 的代理可按各自的安装方式使用。

## 使用

在具备本地文件、命令执行权限的代理中调用，例如：

```text
使用 $video-subtitle-translate 处理我指定文件夹的视频。
先检查现有工具和字幕，优先提取已有字幕；没有字幕再选语音识别或 OCR。
由你翻译成中文，输出无黑底的中文字幕成片，保留原视频。
```

也可只生成字幕或只翻译文件名。普通纯文本聊天不能仅靠导入技能就操作本机视频。

首次使用时，技能会引导代理读取[工具下载与安装指南](skills/video-subtitle-translate/references/tools-setup.md)，发现现有依赖，只准备当前任务缺少的部分，并遵循使用者的安装授权。

| 场景 | 主要依赖 |
|---|---|
| 读取媒体信息、提取字幕、压制成片 | FFmpeg / ffprobe |
| 使用内附字幕生成脚本 | Python 3 标准库 |
| 无字幕对白 | 按需安装 faster-whisper 与识别模型 |
| 硬字幕、气泡、日文画面文字 | 按需安装 RapidOCR / Manga OCR 及模型 |
| 默认字幕字体 | 另行下载思源黑体简体中文 |

只翻译已有文字字幕时，不必安装语音/OCR 模型。识别模型仍可能占用较大空间；本技能不捆绑它们，也不包含 Ollama/千问等本地翻译大模型流程。

## 辅助脚本

在技能目录执行：

```text
python scripts/subtitle_json.py translated.json --source original.json --check-only
python scripts/subtitle_json.py translated.json --source original.json --output-dir task/subtitles
```

[数据格式与翻译约定](skills/video-subtitle-translate/references/translation.md) · [排版、成片与核验](skills/video-subtitle-translate/references/finishing.md)

脚本不联网、不识别或翻译原文、不修改/删除视频。没有翻译的条目需显式记录原因；已存在的字幕输出不会被覆盖。复杂气泡布局仍需代理编排和样片检查。

## 限制与文件保护

- 默认保留原视频，任何删除都需要当前使用者明确授权，且对应成片已通过核验。
- 不覆盖同名目标，不根据相似标题自动删重。先核对源身份，再保存源→输出路径对照。
- 硬字幕需要重编码，速度和画质取决于设备及编码方案；HDR、特殊音轨、附件与多视频流需要单独处理。
- OCR/语音识别会出错，完整解码也不证明译文准确或字幕完整；需按技能流程检查。
- 已验证的是技能结构、辅助脚本及合成短片的字幕压制、双音轨保留、完整解码；未在所有系统、GPU 和依赖版本组合上测试。
- 工作方法主要来自 Windows 本地处理；其他系统需调整路径和安装方式。不保证跨聊天无人值守连续执行。
- 使用者自行确保有权处理素材，并遵循所用代理、模型和软件的规则。

## 反馈与许可

可通过 [Issues](https://github.com/yan450863-ui/video-subtitle-translate/issues) 反馈问题。请提供工具版本、简化操作与脱敏错误，不上传私人视频、字幕、密钥或完整个人路径。

技能文字和本仓库自编脚本按 [MIT License](LICENSE) 分享。第三方工具、字体及模型不包含在内，使用和分发时分别遵循其许可证。
