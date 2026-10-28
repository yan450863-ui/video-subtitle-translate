# 排版、成片与核验

## 辅助脚本

只依赖 Python 标准库，不下载软件、不联网、不修改或删除视频。

```text
python scripts/subtitle_json.py translated.json --source original.json --check-only
python scripts/subtitle_json.py translated.json --source original.json --output-dir task/subtitles
```

第二条生成 chinese.ass 和 chinese.srt，已有同名输出时停止，不覆盖。source 用于核对每个 cue 的 ID 与时间轴，建议始终传入。`--duration` 可检查字幕是否超出正片。警告（重叠、长句）需要按画面判断，不自动裁句。

默认样式：思源黑体 CN，白字黑描边，无黑底；1080P 参考坐标、字号 56、左右边距 120、底边距 40、底部居中。可用 `--font`、`--font-size`、`--margin-v` 调整；竖屏用 `--width 1080 --height 1920` 并按样片调整边距。

译文可写真实换行，最多两行。普通文本不接受原始 ASS 标签。需要旁白自定义位置时，给 cue 加 `position: [x, y]`（ASS 参考坐标）和可选的 `alignment: 1..9`；例如 `position: [150, 180], alignment: 7` 表示左上锚点。位置只应用于 ASS，SRT 无法保留；多个气泡/竖排布局需额外编排和样片检查。

## 压制

先确认 `ffmpeg -filters` 含 ass/subtitles，`ffmpeg -encoders` 含计划使用的编码器。检测到 NVIDIA 显卡也不能假设 NVENC 可用，先试短片；没有可用硬编码器时可用 libx264。FFmpeg/ffprobe、模型和字体由使用者单独准备，本技能不包含这些依赖。

下面是普通单视频流、MP4兼容音轨的参考命令。**在任务目录运行，使用简单相对 ASS/字体目录名**，可减少 Windows 滤镜中的盘符转义问题；INPUT/OUTPUT 替换为真实路径，用 subprocess 参数列表传参。

```text
ffmpeg -nostdin -n -i INPUT -vf ass=chinese.ass:fontsdir=fonts -map 0:v:0 -map 0:a? -map_metadata 0 -map_chapters 0 -c:v libx264 -crf 18 -preset medium -c:a copy OUTPUT.processing.mp4
```

这是参考质量起点，不是所有视频的最佳参数。不要默认强制改变帧率、分辨率、位深、HDR 色彩信息或宽高比。高位深/HDR 源片需单独确定编码和色彩流程，不能照搬普通 SDR 配方。可复制音轨时复制全部，保持语言、默认轨/强制轨等标记。没有音轨的片子允许正常压制。

命令示例没有映射原字幕、附加封面、附件或额外视频流；源片有这些内容时先决定保留方式，不能静默省略。文字字幕、图片字幕和附件在 MP4/MKV 中的支持不同；必要时选择 MKV 或保留外挂，并按用户目标处理。

为了检查具体时间点的完整字幕，短样片可直接用完整滤镜渲染后输出 seek；若输入端 `-ss` 会重置字幕时间，则先生成时间偏移正确的样片 ASS，或按已验证方案恢复绝对 PTS。不要因为错误 seek 得到“无字幕样片”就判断译文缺失。先看长句、第一句、最后一句、原字幕冲突处及旁白位置。

## 发布前

1. ffprobe 核对源片与成片的时长、分辨率/显示比例、帧率、音轨数量与语言；容差按源时间基合理设置，不对长片使用宽泛百分比掩盖缺尾。
2. 检查每个提取 ID 已有翻译或排除原因，按任务核对 OCR 扫描区域与时间覆盖；确认字体实际解析为目标字体而不是缺字回退。
3. 完整解码成片一次，保存日志和退出码：

```text
ffmpeg -nostdin -v error -xerror -i OUTPUT.processing.mp4 -map 0:v:0 -map 0:a? -f null -
```

解码通过只证明能解码，不证明译文正确。完整解码有成本，无变化且已通过的成片不重复验证。

4. 全部通过才更名为最终文件；目标已存在则停止处理冲突。保存源身份、成片身份、参数、字幕数、核验结果和旧名→新名映射。
5. 分享版默认不删除原件。当前用户明确授权清理时，重新核对源文件身份、成片与源不是同一路径、核验已通过，精确清理对应原件并保存记录；不能用递归通配删除，也不能顺便清理“类似文件”。

## 分享与使用

将整个 `video-subtitle-translate` 文件夹放到接收者当前客户端的技能目录。当前 Codex 官方列出的个人目录为 `~/.agents/skills/`，项目目录为 `.agents/skills/`；旧版或自定义安装器可能使用 `~/.codex/skills/`，以实际配置为准。重新加载后用 `$video-subtitle-translate` 调用。其他支持 SKILL.md 的代理也可按各自的技能目录使用；它是流程技能，不是独立 GUI 或自带运行环境的软件。首次准备工具时读取 [tools-setup.md](tools-setup.md)，里面有官方下载入口、按需安装和最小使用示例。

压缩包只包含技能文本与自编辅助脚本，不含私人字幕/视频/截图/绝对路径，不包含字体/模型权重或第三方二进制，也不包含已放弃的本地翻译模型工作流。使用者自行准备其任务需要的工具；若另行分发这些工具/模型，应单独保留相应许可并遵守分发条件。
