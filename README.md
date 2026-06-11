# 新北市學區收入儀表板

以新北市里級綜所稅資料與公立國中小學區對照表，建立可公開分享的 Streamlit 儀表板。

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

這是一個 Streamlit 互動儀表板，正式互動版建議部署到 Streamlit Community Cloud：

1. 將此 repo 推到 GitHub。
2. 到 Streamlit Community Cloud 新增 app。
3. 選擇此 repo，入口檔案設定為 `app.py`。
4. Python dependencies 會由 `requirements.txt` 安裝。

GitHub Pages 只支援靜態網站，無法直接執行 Streamlit app。本 repo 另外提供 `docs/index.html` 作為 GitHub Pages 的靜態說明頁，可用來放專案介紹與互動版連結。

## Data

- `school/*_165-F.csv`: 107-112 年綜稅綜合所得總額各縣市鄉鎮村里統計分析表。
- `school/school_zones.csv`: 學區對照表。

`school_zones.csv` 欄位固定為：

```text
學年度,學制,行政區,學校名稱,學區類型,村里,鄰里備註,資料來源
```

`學區類型` 可填：

- `基本學區`
- `自由學區`
- `共同學區`
- `特殊規則`

首頁排名只使用 `基本學區`。自由/共同學區會在學校頁以參考情境呈現，不進主排名。

目前資料已納入 107-112 年新北市里級收入資料，以及 115 學年度公立國中小學區 PDF 轉出的學區對照。
