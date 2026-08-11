# TW Social Short Video Editor

一個可重複使用的 Codex Skill，把繁體中文口播素材整理成適合 Instagram Reels、YouTube Shorts 與 Facebook Reels 的 9:16 短影音。

目前版本：`v1.2.0`

它把實際九輪剪輯回饋整理成可移植流程：本機優先與雲端備援轉錄、逐字時間碼快取、金句與重複段落分析、金句冷開場、語意字幕斷行、分段變速、IG 安全區、精準特效與音效、720p 預覽核准，以及從原始高解析素材重建並驗證 1080×1920 正式版。

## 特色

- 逐字時間碼與完整字詞邊界剪輯
- 本機 `faster-whisper` 優先；取得單檔同意後才允許 OpenAI `whisper-1` 雲端備援
- 依來源影片 SHA-256 快取逐字稿，避免重複轉錄與費用
- 自動產生金句候選、重複內容、贅詞／片段標記與段落重組初稿
- 55–60 秒分段變速規劃，預設清晰度上限 1.25×
- 繁體中文字幕語意斷行與雙行排版
- 可選用 `phoebe-v1` 饅頭黑體風格
- IG 安全區檢查工具
- 字幕、特效與音效時間軸重算工具
- 雲端轉錄同意、隱私保護、預覽核准與正式檔 QA
- 一次填寫的創作者風格設定檔，以及每支影片使用的簡短製作單
- 第一次使用由 AI 對話引導建立設定檔，不必自己尋找模板位置
- 一次確認後建立隔離的本機轉錄環境；不改動既有 Python，也不需要管理員權限
- 優先沿用電腦現有的 FFmpeg；缺少時才準備 Skill 專用 FFmpeg/ffprobe
- 設定檔、模型與執行環境放在 Skill 外部，更新時可保留

## 學員客製化公版

學員可以自由調整字體、字幕顏色、重點字、音效、視覺特效、貼圖、語速與轉場。第一次啟用時，AI 會檢查設定檔是否存在；沒有的話直接用對話帶你填，不需要進安裝資料夾找檔案。設定分成兩層：

1. 由 AI 引導建立固定品牌風格；也可上傳已填好的 [`creator-style-profile-template.md`](skills/tw-social-short-video-editor/assets/creator-style-profile-template.md)。
2. 每支影片複製 [`video-brief-template.md`](skills/tw-social-short-video-editor/assets/video-brief-template.md)，只填主題、受眾、片長與本次臨時調整。

套用順序為「單支影片製作單 ＞ 創作者風格設定檔 ＞ Skill 預設」。不確定的欄位可填「請依影片主題建議」。轉錄同意、內容不失真、安全區、預覽核准與正式檔 QA 不會被個人設定關閉。

## 第一次使用與本機環境

- Codex
- 雲端備援：`OPENAI_API_KEY`；每一支來源影片都必須先取得同意

Skill 會先做唯讀檢查。若本機環境未完成，AI 會把以下內容合併成一次確認：

- 在 Skill 外部建立獨立 Python 環境
- 安裝固定版本的 `faster-whisper`
- 下載 `small` 模型
- 只有系統找不到 `ffmpeg` 或 `ffprobe` 時，才下載 Skill 專用版本

確認後自動準備，不會把套件裝進原本的 Python，也不會更改全域 `PATH`。由於 FFmpeg 執行檔與模型來自其上游來源，首次下載時間與容量會依平台和網路而異。

可手動執行唯讀檢查：

```bash
python skills/tw-social-short-video-editor/scripts/setup_runtime.py --check
```

在使用者同意整組本機下載後執行：

```bash
python skills/tw-social-short-video-editor/scripts/setup_runtime.py \
  --install --confirm-local-downloads --model small
```

API key、`.env`、原始影片和逐字稿都不應提交到 GitHub。

## 自動轉錄與段落重組

只允許本機轉錄：

```bash
python skills/tw-social-short-video-editor/scripts/transcribe_video.py input.mov \
  --provider local \
  --output edit/transcripts/input.json
```

本機優先、雲端備援：

```bash
export OPENAI_API_KEY="your-key"
python skills/tw-social-short-video-editor/scripts/transcribe_video.py input.mov \
  --provider auto \
  --cloud-consent \
  --output edit/transcripts/input.json
```

`--cloud-consent` 代表已針對該檔案取得上傳同意，不能預先寫進固定指令或設定檔。雲端路徑只上傳由 FFmpeg 擷取與壓縮的單聲道音訊，不上傳原始影像。

產生 45–50 秒段落初稿：

```bash
python skills/tw-social-short-video-editor/scripts/analyze_transcript.py \
  edit/transcripts/input.json \
  --output edit/story-plan.json \
  --target-seconds 50 \
  --max-speed 1.15
```

分析結果是可審核初稿，不是最終剪輯決策；仍須確認金句前移後沒有改變原意，並逐一播放剪點。

## 安裝

在 Codex 中說：

> 請從 `https://github.com/phoebe-sky/tw-social-short-video-editor/tree/main/skills/tw-social-short-video-editor` 安裝這個 Skill。

或使用內建安裝器：

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo phoebe-sky/tw-social-short-video-editor \
  --path skills/tw-social-short-video-editor
```

安裝後開啟新的 Codex 對話，並輸入：

> 使用 `$tw-social-short-video-editor`，把我的口播素材剪成 55–60 秒、適合 IG／YT／FB 的直式短影音。

第一次使用時，AI 會主動檢查並引導建立創作者設定檔。之後也可以直接說「顯示我的創作者設定」、「修改重點色」或「匯出創作者設定檔」。

## 如何取得 Skill 更新

GitHub 安裝的是一份本機副本，不會因為此儲存庫有新 commit 就自動同步。需要新版本時，重新執行上面的安裝指令或產品內的更新動作即可。創作者設定檔、`small` 模型與隔離環境存放在 Skill 之外，正常更新不會覆蓋它們。

## 儲存庫結構

```text
skills/
└── tw-social-short-video-editor/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    ├── scripts/
    └── assets/
```

## 授權

Skill 文字與程式碼採用 [MIT License](LICENSE)，可自由使用、修改與分享。

內附的饅頭黑體不適用 MIT License，依字型資料夾內的 SIL Open Font License 1.1 再散布。
