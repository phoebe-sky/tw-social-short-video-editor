# TW Social Short Video Editor

一個可重複使用的 Codex Skill，把繁體中文口播素材整理成適合 Instagram Reels、YouTube Shorts 與 Facebook Reels 的 9:16 短影音。

它把實際九輪剪輯回饋整理成可移植流程：金句冷開場、語意字幕斷行、分段變速、IG 安全區、精準特效與音效、720p 預覽核准，以及從原始高解析素材重建並驗證 1080×1920 正式版。

## 特色

- 逐字時間碼與完整字詞邊界剪輯
- 55–60 秒分段變速規劃，預設清晰度上限 1.25×
- 繁體中文字幕語意斷行與雙行排版
- 可選用 `phoebe-v1` 饅頭黑體風格
- IG 安全區檢查工具
- 字幕、特效與音效時間軸重算工具
- 雲端轉錄同意、隱私保護、預覽核准與正式檔 QA
- 一次填寫的創作者風格設定檔，以及每支影片使用的簡短製作單

## 學員客製化公版

學員可以自由調整字體、字幕顏色、重點字、音效、視覺特效、貼圖、語速與轉場。建議使用兩層設定：

1. 先複製並填寫 [`creator-style-profile-template.md`](skills/tw-social-short-video-editor/assets/creator-style-profile-template.md)，建立自己的固定品牌風格。
2. 每支影片複製 [`video-brief-template.md`](skills/tw-social-short-video-editor/assets/video-brief-template.md)，只填主題、受眾、片長與本次臨時調整。

套用順序為「單支影片製作單 ＞ 創作者風格設定檔 ＞ Skill 預設」。不確定的欄位可填「請依影片主題建議」。轉錄同意、內容不失真、安全區、預覽核准與正式檔 QA 不會被個人設定關閉。

## 需求

- Codex
- FFmpeg 與 `ffprobe`
- 能輸出逐字起訖時間的轉錄方式；使用雲端服務前必須逐檔取得同意

API key、`.env`、原始影片和逐字稿都不應提交到 GitHub。

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
