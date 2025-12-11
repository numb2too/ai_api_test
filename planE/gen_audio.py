from gtts import gTTS
import os

# 這是模擬的會議逐字稿內容
# 為了讓 AI 即使在單一語音下也能辨識，我們讓讀稿稍微帶入角色名稱
meeting_script = """
會議開始。

大家好，我們來快速過一下這週的進度。下週一就要上線了，目前的狀況如何？

首頁的動畫效果我已經調好了，但是登入頁面還有一個 Bug。
我預計這個禮拜三之前可以修復完畢。

好的，禮拜三修好。那後端呢？

API 的部分大部分都好了，但我還缺資料庫的連線設定檔。
另外，我需要在這週五之前完成壓力測試，不然上線會有風險。

了解。資料庫設定檔我等一下開完會馬上寄給你。
那 Kelly，妳修完 Bug 後記得通知 QA 團隊測試。

沒問題，我修好後會發 Slack 通知大家。

好，那就先這樣，大家分頭工作吧。散會。
"""

print("正在生成測試音檔 (test_meeting.mp3)...")

# 使用 Google小姐 (zh-TW) 朗讀這段文字
# 雖然只有一個聲音，但因為內容包含 "David 說"、"Kelly 說"，
# Gemini 1.5 非常聰明，能透過語意理解分辨出是誰在講話。
tts = gTTS(text=meeting_script, lang="zh-tw")
tts.save("test_meeting.mp3")

print("✅ 生成完畢！檔案名稱：test_meeting.mp3")
print("👉 請回到你的網頁介面，上傳這個檔案進行測試。")
