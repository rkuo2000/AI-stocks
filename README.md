# AI-stocks
![](https://cf-assets2.tenlong.com.tw/products/images/000/195/999/webp/9789863127727_%E5%A4%A9%E7%93%8F.webp?1699843474)

[最強 AI 投資分析：打造自己的股市顧問機器人，股票趨勢分析×年報解讀×選股推薦×風險管理](https://www.tenlong.com.tw/products/9789863127727)


## [CH1.股票分析基礎](https://github.com/rkuo2000/AI-stocks/blob/main/CH1_%E8%82%A1%E7%A5%A8%E5%88%86%E6%9E%90%E5%9F%BA%E7%A4%8E%20.md)

## [CH2. 大型語言模型界面](https://github.com/rkuo2000/AI-stocks/blob/main/CH2_%E5%A4%A7%E5%9E%8B%E8%AA%9E%E8%A8%80%E6%A8%A1%E5%9E%8B%E7%95%8C%E9%9D%A2.md)

## CH3. 股市資料蒐集、爬蟲與搭建資料庫
[ch03_stock_crawler.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch03_stock_crawler.ipynb)<br>

### 證交所資料爬蟲
進入證交所網址：[https://www.twse.com.tw/zh/index.html](https://www.twse.com.tw/zh/index.html)<br>
使用開發者模式取得請求資料網址<br>
* 取得個股日成交資訊
* 取得連續月份資料(以個股本益比為例)

### 用 BeautifulSoup4 取得 Yahoo 股市資料
* 取得當日股價
* 取得季報表資訊

### 使用 selenium 做新聞爬蟲
* 用 requests 取得股票新聞
* 使用 Selenium 取得股票新聞 (無法執行)
* 使用 yfinance 下載股市資料
* 取得公司基本資料
* 取得損益表
* 取得法人持股比例

### 使用 FinMind 下載股市資料
* **輸入 FinMind API 和帳號密碼**
* 取得股價資料
* 取得損益表資料
* 取得法人買賣資料
* **使用 FinLab 下載股市資料**
* 取得收盤價
* 選擇產業
* 取得財報資料
* 取得法人資料

### SQL資料庫
* 開SQLite3
* 設定資料庫結構
* 傳入資料到資料庫
* 查詢表格資料

---
## CH4.讓 AI 計算技術指標及資料視覺化
[ch04_stock_index_gemini.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch04_stock_index_gemini.ipynb)<br>

### 技術指標公式太複雜？讓 AI 自動化計算

### 讓 AI 自動生成技術指標程式碼
* 計算移動平均線(MA)
* 計算 MACD
* 計算 RSI
* 計算布林通道
* 能量潮指標 (On-Balance Volumem, OBV)

### 讓 AI 自動統整 Dataframe
* 將日頻資料轉換成月頻資料

---
### 資料視覺化

#### 使用 matplotlib 畫出收盤價的折線圖
* 加入成交量
* 加入技術指標
* 繪製 K 線圖：mplfinance
* 選擇資料時間
* 用 mplfinance 繪製 K 線圖
* 加入繪圖設定
* 加入子圖

#### plotly 互動式圖表
* 繪製互動式 K 線圖
* 移除非交易日空值
* 加入懸停十字軸
* 加入技術指標
* 寫成函式
* 執行函式 `plotly_stock("2317", start='2022-01-01', end= None, indicator='布林通道及MACD')`

---
## CH5. AI技術指標回測
[ch05_stock_backtesting_gemini.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch05_stock_backtesting_gemini.ipynb)<br>

### 回測(Backtesting)
回測也稱為回溯測試，是指用歷史數據測試某種交易策略的過去表現，觀察如果時間回溯到過去執行同樣的策略，會產生什麼結果，藉此評估一個策略在未來是否可行，以及提前了解可能的風險。<br>
如果回測後發現，一個策略在過去按照一樣的方法執行，得到的成果很好，那也許它有機會繼續在未來創造好的表現 (但並非絕對)。<br>
而一個策略，回測發現它在過去表現得很差，代表存在某些缺陷，我們就不會採用這個策略，因為對它未來的表現不會有信心。<br>

回測是把自己想的交易方法，透過歷史數據進行測試，藉由查看回測結果(過去表現)，了解一個交易方法的可行性和有效性。<br>
理論上，一個未來能賺錢的投資策略，至少要在過去也能賺錢，回測就是驗證的方式。<br>
策略經過歷史模擬，更能歷久不衰，獲取超額報酬！<br>

---
### [FinLab](https://ai.finlab.tw/)
FinLab 提供台股 Python 量化交易最前瞻的技術、資料庫、演算法，幫助您開發選股策略，獲取超額報酬：<br>
* 完整的股價、營收、籌碼、財報資料庫
* 超多範例，快速程式碼開發策略
* 策略儀表版

---
### 回測結果分析

```
stats = ai_backtest(stock_id="2330.TW",
           period="5y",
           user_msg="MACD",
           add_msg="請設置10%的停損點與20%的停利點")
reply = backtest_analysis(stats)
print(reply)
```

---
### 比較多個策略

```
# 策略1:MACD+停利停損
stats1 = ai_backtest(stock_id="2330.TW", period="5y",
            user_msg="MACD",
            add_msg="請設置10%的停損點與20%的停利點")
# 策略2:SMA
stats2 = ai_backtest(stock_id="2330.TW", period="5y",
            user_msg="SMA",
            add_msg="無")
# 策略3:RSI+停利停損
stats3 = ai_backtest(stock_id="2330.TW", period="5y",
            user_msg="RSI",
            add_msg="請設置10%的停損點與20%的停利點")

reply = backtest_analysis(stats1, stats2, stats3)
print(reply)
```

---
## CH6. 個股分析機器人
[ch06_stock_bot_gemini.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch06_stock_bot_gemini.ipynb)<br>

* 取得股價資料
* 取得基本面資料
* 取得新聞資料
* 爬取股號、股名對照表
* 取得股票名稱
* 建構 ChatGPT 模型
* 大盤趨勢報告
* 個股分析報告
* 雞蛋水餃股也能做分析

---
### [AI股票分析師](https://ai.studio/apps/drive/15h6gss2NLZeahDZHuX67eww1SiC_70Xo)

**Prompt**: `AI股票分析師: 輸入股票代號, 分別從鉅亨網抓取新聞 json_data = requests.get(f'https://ess.api.cnyes.com/ess/api/v1/news/keyword?q={stock_name}&limit=5&page=1').json(),由 yfinance 獲取基本面資料及股價資訊 df = yf.Ticker(stock_id).history(start=start)`
![](https://github.com/rkuo2000/AI-stocks/blob/main/images/AI_Stock_Analyst.png?raw=true)

---
## CH7. 年報問答機器人
**[年報下載網站](https://doc.twse.com.tw/server-java/t57sb01)** <br>

[ch07_annual_reporter.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch07_annual_reporter.ipynb)<br>

* 建立函式-取得年報
* 年報問答RAG
* 年報總結與分析

---
### [財報機器人](https://ai.studio/apps/drive/16bUHToD_mTgp_HrlIKPSZQ5AvzkxSzyW)

**Prompt**: `財報機器人：輸入台灣股票代號及年份，按鍵打開 https://doc.twse.com.tw/server-java/t57sb01 網頁，上傳年報 pdf, 然後進行財報之問答與分析`<br>
![](https://github.com/rkuo2000/AI-stocks/blob/main/images/Financial_Report_Bot.png?raw=true)

---
## CH8. 建構投資組合：讓 AI 輔助選股
[ch08_stock_picking.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch08_stock_picking.ipynb)<br>

* 下載資料庫
* 檢視資料表格式
* AI 自動化選股機器人
* 趨勢報告推薦系統 : 取得個股分析報告, 
* 推薦出一檔股票
* 推薦股票的評分排序
* AI 年報分析推薦系統
* 多檔股票的年報分析報告
* 根據分析結果推薦出一檔股票
* 年報分析報告評分排序

---
## CH9. 讓 AI 評估投資組合風險 
[ch09_portfolio_risk.ipynb](https://github.com/rkuo2000/AI-stocks/blob/main/ch09_portfolio_risk.ipynb)<br>

### 資金管理
* 單次賭局的期望資產
* 單一賭局的隨機結果
* 重複賭局的資產變化
* 不同下注量的資產成長幅度
* 倍倍下注法
* 凱利公式 Kelly formula
* 取得回測結果
* 計算賠率、取得勝率及最佳下注比例
* 用凱利公式來更改策略

---
### 投資組合資金分配與風險管理
* 資金管理
* 設定投資組合
* 計算每月的漲幅或跌幅
* 計算每檔股票的最佳下注比例
* 比較平均分配與使用下注比例的報酬
* 與大盤績效進行比較
* 投資組合標準差 (σ)
* 風險值 (Value at Risk, VaR)
* beta 係數 (β)
* 夏普比率 (Sharpe Ratio)
