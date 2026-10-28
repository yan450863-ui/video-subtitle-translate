# 按内容提取

## 先定位与探测

用 Python subprocess 参数列表或等效安全调用传入路径；Windows 上带方括号、日文、空格的路径不要当成通配符或拼接成 shell 命令。ffprobe 输出保存为 JSON：

```text
ffprobe -v error -show_format -show_streams -of json INPUT
```

从 streams 确定视频、音频和字幕的索引/语言/编码，多个音轨先试听选定语言。不要把封面 attached_pic 当正片。大小+mtime 适合判断任务是否需要重跑，不证明内容完全相同。

## 内嵌/外挂文字字幕

按实际索引提取，例如首个文字字幕轨：

```text
ffmpeg -nostdin -n -i INPUT -map 0:s:0 subtitles.srt
```

ASS 转 SRT 会损失位置、样式和特效；需要保留复杂布局时另存原 ASS。PGS/VobSub 等图片字幕不能直接当文本转出，需要图片字幕 OCR。检查语言和全片覆盖后再翻译，不只根据轨道标签判断。

## 无字幕对白：faster-whisper

选择符合本机资源的模型/计算类型，CPU 可先试 int8，CUDA 能否使用取决于驱动与运行依赖，不能直接复制旧电脑的 float16 配置。先确认语言，混合语言片段分开处理。

经验：长静音、音乐、喘息可能产生幻觉或重复长句。VAD 分离有声片段，采用有界短块（例如约 20～30 秒，按句边界调整）并保留绝对时间偏移；`condition_on_previous_text=False` 可用于减少反复输出。它不是准确性保证，不凭一条置信阈值自动删对白。

参考调用形状（根据已安装版本核对参数）：

```python
from faster_whisper import WhisperModel
model = WhisperModel(model_path, device=device, compute_type=compute_type)
segments, info = model.transcribe(
    clip_path, language=language, vad_filter=True,
    condition_on_previous_text=False, beam_size=5,
)
for s in segments:
    # offset 是当前音频块在原视频中的起点；整片输入时为 0。
    save_cue(offset + s.start, offset + s.end, s.text)
```

跨块边界可轻微重叠，但必须按时间与文字去重；不能只凭相同文本删除不同时刻的真实重复对白。按块保存完成状态，避免中断后从头跑。全片原音轨保留，无法可靠识别的句子记录不确定性。

## 硬字幕和气泡：OCR

- 先看有代表性的画面，确定字幕/旁白/气泡所在区域；底部日文字幕只裁底部，气泡/竖排文字则需扫描相应区域或全画面，不能套用固定底部裁剪。
- RapidOCR 可检测文字区域；日文花体/竖排识别可试 Manga OCR。输入应尽量是紧凑、清晰的文字裁图，按画面阅读顺序组织，而不是混合整屏多块文字。
- 每秒 1 帧可作为粗扫起点，但会漏掉短句。发现切换快的段落后提高采样，细查文本进入和消失边界。不把“出现少于两秒”作为自动丢弃条件。
- 记录采样时间、区域、原识别文字、置信度及裁图引用；邻近相同文字合并为持续区间。相似但关键字不同的句子不要过度合并。
- 对变化少的相同裁图可缓存识别；仅根据粗识别字符串相似度缓存容易传播错字。保留原始 observations，合并规则变更时重建 cue 即可，不必重扫视频。
- 检查拟声、标牌、工牌等是否在用户要求内。翻译剧情文字，避免将水印或界面杂字混入对白。

源片存在截断、读帧错误时，记录能读取的范围；不得把局部提取完成报告为全片完成。只为未解决的具体问题做局部复查。
