# 工具下载、安装与最小使用

面向有本地文件和命令执行能力的代理。以下是 Windows/PowerShell 示例，其他平台使用官方对应安装方法。先读机器环境；这些命令是操作指南，不会因读取技能而自动执行。按当前用户的授权安装所需组件，优先复用已有环境。

## 按任务选择

| 任务 | 需要的组件 |
|---|---|
| 仅改文件名 | 代理的文件工具；需查参数时用 ffprobe |
| 文字字幕翻译 | 提取内嵌字幕用 FFmpeg；本技能字幕生成脚本用 Python；已有外挂字幕不必识别 |
| 刻入字幕 | FFmpeg（含 libass 和可用编码器）、ffprobe、字体 |
| 无字幕对白 | 另加 faster-whisper 和多语言 Whisper 模型 |
| 硬字幕/气泡 | 另加 RapidOCR；需要日文精细识别时加 Manga OCR |

不安装本地大语言翻译模型，翻译由当前助手完成；Whisper/OCR 的识别权重仍需按实际任务下载。技能包小不意味着识别无需模型。

## 1. 检查现有环境

```powershell
Get-Command python,py,ffmpeg,ffprobe -ErrorAction SilentlyContinue
python --version
ffmpeg -version
ffprobe -version
ffmpeg -hide_banner -filters
ffmpeg -hide_banner -encoders
```

缺少命令时查用户指定的工具目录。python 可能是 Windows 商店别名，以实际可执行的解释器为准。滤镜需有 ass/subtitles，编码器需有计划使用的 libx264 或硬件编码器。发现路径后保存为配置，不必改全局 PATH。检测到显卡不代表 CUDA/NVENC 已能运行。

## 2. Python

来源：[Python Windows 官方下载页](https://www.python.org/downloads/windows/)。选架构匹配且依赖支持的版本，不盲目追最新。兼容环境可从 64 位 Python 3.11/3.12 着手，具体可安装版本以当前官方页面和依赖支持为准。

在用户选定的工具目录创建独立环境，下面 python 必须指向选好的解释器：

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
```

后文命令假设仍在此目录执行，显式调用环境的 python，无需激活环境或修改执行策略。把路径、版本、缓存及模型目录保存到配置；不把下载的模型放进技能包。

## 3. FFmpeg / ffprobe

入口：[FFmpeg 官方下载页](https://ffmpeg.org/download.html)。项目提供源码，Windows 页面链接到 gyan.dev/BtbN 的预编译构建；选架构匹配的可执行程序包，不误下载源码。

将包含 ffmpeg.exe、ffprobe.exe 的包解压到用户选定的 tools/ffmpeg 等目录，核对来源及发布方提供的校验信息，再用绝对路径执行 version/filters/encoders 检查。便携版不需要安装开发工具链。

提取、压制、解码命令分别见 extraction.md 和 finishing.md。faster-whisper 自身用 PyAV 解码，不一定需要系统 FFmpeg；但本技能的字幕提取、画面取样和成片仍用 FFmpeg。

## 4. 字体

来源：[Adobe 思源黑体官方项目](https://github.com/adobe-fonts/source-han-sans)的 Releases/下载指引。取简体中文 OTF 或适合的地区子集，先选 Medium 或 Regular，不必下全部字重。放进任务 fonts/ 目录，用 `ass=chinese.ass:fontsdir=fonts` 加载，无需全局安装。

ASS Fontname 要匹配实际字体内部家族名，不能把文件名随意当家族名。查看 libass 的字体选择日志并看中文样片，确认未回退或缺字；字体许可随下载文件保留。

## 5. 语音识别（仅无可用字幕对白时）

安装与硬件要求：[faster-whisper 官方仓库](https://github.com/SYSTRAN/faster-whisper)。

```powershell
& '.\.venv\Scripts\python.exe' -m pip install faster-whisper
& '.\.venv\Scripts\python.exe' -c "import faster_whisper, ctranslate2; print('ASR imports OK')"
```

首次使用模型名会下载权重；已有模型时传本地目录复用。先说明大小、保存位置与计算方案，按当前授权下载。日语/英语任务选多语言模型，不用 `.en` 英语专用模型处理日语。安装包成功不等于模型已就绪。

在独立环境中运行以下短片初测形状，实际代码补上导入与 JSON 保存，不能把所有长片都一次性处理：

```python
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8',
                     download_root='models/whisper')
segments, info = model.transcribe('sample.mp4', task='transcribe',
    vad_filter=True, condition_on_previous_text=False)
cues = [{'id': f'c{i:06d}', 'start': s.start, 'end': s.end, 'text': s.text.strip()}
        for i, s in enumerate(segments, 1)]
```

需迭代 segments 才真正识别，输出依然是原语言。保存 cues 后接 translation.md。CPU 示例适合检查可用性，不保证长片速度或最佳准确率。GPU 依赖按官方当前 CTranslate2/CUDA/cuDNN 兼容说明配置，Windows 不直接套 Linux 的库安装和路径设置。长片按 extraction.md 分块保存进度。

## 6. OCR（仅硬字幕/气泡时）

来源：[RapidOCR 官方仓库](https://github.com/RapidAI/RapidOCR)、[Manga OCR 官方仓库](https://github.com/kha-white/manga-ocr)。先用 CPU 后端与一张字幕裁图验证。

```powershell
& '.\.venv\Scripts\python.exe' -m pip install rapidocr onnxruntime
& '.\.venv\Scripts\python.exe' -c "from rapidocr import RapidOCR; print('OCR import OK')"
```

当前 RapidOCR 最小调用：`from rapidocr import RapidOCR; result = RapidOCR()('crop.png')`。初始化可能下载模型。先核对语言模型及实际结果结构；旧 `rapidocr_onnxruntime` 与新 `rapidocr` 的接口不同，不混用。默认识别器不保证读日文，可仅用它检测文字框，再裁图交给日文识别器。

需要日文精细识别时才安装：

```powershell
& '.\.venv\Scripts\python.exe' -m pip install manga-ocr
& '.\.venv\Scripts\python.exe' -c "from manga_ocr import MangaOcr; print('Manga OCR import OK')"
```

测试：`from manga_ocr import MangaOcr; print(MangaOcr()('japanese-crop.png'))`。初始化通常还要下载识别权重；按官方支持选择 Python/PyTorch。旧项目使用 transformers 4.x，复用旧代码要隔离兼容环境，不能在别人现有环境中盲目降级。Manga OCR 不自动定位视频里的气泡，空白图也可能输出假文字，先确认裁图确实有字。

## 7. 安装完成的判断

记录实际版本、路径、模型目录与环境变量。验证相关模式能读真实文件、生成文字/时间轴；需要刻入时，还要验证字体、压制短片和解码。仅导入成功不等于端到端可用；通过的部分不重复安装。

若代理没有本地工具权限，只能指导操作或翻译已提取文字，不能声称已经下载或处理视频。离线或下载失败时保留任务进度，说明需要的包/模型，不擅自改用付费服务。新机器的安装兼容性仍需现场验证，本技能不保证任意硬件组合都能一键运行。
