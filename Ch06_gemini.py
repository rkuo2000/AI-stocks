import getpass
import openai
from openai import OpenAI
import tiktoken
import yfinance as yf
import numpy as np
import requests
import os
import datetime as dt
from bs4 import BeautifulSoup
import pandas as pd

GEMINI_API_KEY = ' '

class StockInfo():
  # 取得全部股票的股號、股名
  def stock_name(self):
    # print("線上讀取股號、股名、及產業別")
    response = requests.get('https://isin.twse.com.tw/isin/C_public.jsp?strMode=2')
    url_data = BeautifulSoup(response.text, 'html.parser')
    stock_company = url_data.find_all('tr')
  
    # 資料處理
    data = [
        (row.find_all('td')[0].text.split('\u3000')[0].strip(),
          row.find_all('td')[0].text.split('\u3000')[1],
          row.find_all('td')[4].text.strip())
        for row in stock_company[2:] if len(row.find_all('td')[0].text.split('\u3000')[0].strip()) == 4
    ]
  
    df = pd.DataFrame(data, columns=['股號', '股名', '產業別'])
  
    return df
  # 取得股票名稱
  def get_stock_name(self, stock_id, name_df):
      return name_df.set_index('股號').loc[stock_id, '股名']

class StockAnalysis():
  def __init__(self,openai_api_key):
    # 初始化 OpenAI API 金鑰
    self.client = OpenAI(api_key=userdata.get('GEMINI_API_KEY'),
                         base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    self.stock_info = StockInfo()  # 實例化 StockInfo 類別
    self.name_df = self.stock_info.stock_name()
  # 從 yfinance 取得一周股價資料
  def stock_price(self, stock_id="大盤", days = 15):
    if stock_id == "大盤":
      stock_id="^TWII"
    else:
      stock_id += ".TW"
  
    end = dt.date.today() # 資料結束時間
    start = end - dt.timedelta(days=days) # 資料開始時間
    # 下載資料
    df = yf.download(stock_id, start=start)
  
    # 更換列名
    df.columns = ['開盤價', '最高價', '最低價',
                  '收盤價', '調整後收盤價', '成交量']
  
    data = {
      '日期': df.index.strftime('%Y-%m-%d').tolist(),
      '收盤價': df['收盤價'].tolist(),
      '每日報酬': df['收盤價'].pct_change().tolist(),
      # '漲跌價差': df['調整後收盤價'].diff().tolist()
      }
  
    return data
  # 基本面資料
  def stock_fundamental(self, stock_id= "大盤"):
    if stock_id == "大盤":
        return None
  
    stock_id += ".TW"
    stock = yf.Ticker(stock_id)
  
    # 營收成長率
    quarterly_revenue_growth = np.round(stock.quarterly_financials.loc["Total Revenue"].pct_change(-1).dropna().tolist(), 2)
  
    # 每季EPS
    quarterly_eps = np.round(stock.quarterly_financials.loc["Basic EPS"].dropna().tolist(), 2)
  
    # EPS季增率
    quarterly_eps_growth = np.round(stock.quarterly_financials.loc["Basic EPS"].pct_change(-1).dropna().tolist(), 2)
  
    # 轉換日期
    dates = [date.strftime('%Y-%m-%d') for date in stock.quarterly_financials.columns]
  
    data = {
        '季日期': dates[:len(quarterly_revenue_growth)],  # 以最短的數據列表長度為准，確保數據對齊
        '營收成長率': quarterly_revenue_growth.tolist(),
        'EPS': quarterly_eps.tolist(),
        'EPS 季增率': quarterly_eps_growth.tolist()
    }
  
    return data
  # 新聞資料
  def stock_news(self, stock_name ="大盤"):
    if stock_name == "大盤":
      stock_name="台股 -盤中速報"
  
    data=[]
    # 取得 Json 格式資料
    json_data = requests.get(f'https://ess.api.cnyes.com/ess/api/v1/news/keyword?q={stock_name}&limit=6&page=1').json()
  
    # 依照格式擷取資料
    items=json_data['data']['items']
    for item in items:
        # 網址、標題和日期
        news_id = item["newsId"]
        title = item["title"]
        publish_at = item["publishAt"]
        # 使用 UTC 時間格式
        utc_time = dt.datetime.utcfromtimestamp(publish_at)
        formatted_date = utc_time.strftime('%Y-%m-%d')
        # 前往網址擷取內容
        url = requests.get(f'https://news.cnyes.com/'
                          f'news/id/{news_id}').content
        soup = BeautifulSoup(url, 'html.parser')
        p_elements=soup .find_all('p')
        # 提取段落内容
        p=''
        for paragraph in p_elements[4:]:
            p+=paragraph.get_text()
        data.append([stock_name, formatted_date ,title,p])
    return data
    
  # 建立 GPT 3.5-16k 模型
  def get_reply(self, messages):
    try:
      response = self.client.chat.completions.create(
          model="gpt-3.5-turbo",
          temperature=0,
          messages=messages
      )
      reply = response.choices[0].message.content
    except openai.OpenAIError as err:
      reply = f"發生 {err.type} 錯誤\n{err.message}"
    return reply
  
    # 設定 AI 角色, 使其依據使用者需求進行 df 處理
  def ai_helper(self,user_msg):
  
      code_example ="""
    def calculate(table_company, table_daily, table_quarterly):
        table_quarterly['營業收入'] = pd.to_numeric(table_quarterly['營業收入'], errors='coerce')
        latest_two_dates = table_quarterly['日期'].drop_duplicates().sort_values(ascending=False).head(2)
        recent_two_quarters_data = table_quarterly[table_quarterly['日期'].isin(latest_two_dates)].copy()
        recent_two_quarters_data['營業收入成長率'] = recent_two_quarters_data.groupby('股號')['營業收入'].pct_change()
        df_company_with_growth_rate = pd.merge(table_company, recent_two_quarters_data[['股號', '營業收入成長率']], on='股號', how='left')
        df_company_with_growth_rate['市值'] = pd.to_numeric(df_company_with_growth_rate['市值'], errors='coerce')
        top_10_percent_market_cap = df_company_with_growth_rate.nlargest(int(len(df_company_with_growth_rate) * 0.1), '市值')
        top_10_growth_stocks = top_10_percent_market_cap.sort_values(by='營業收入成長率', ascending=False).head(10)
  
        return top_10_growth_stocks
      """
  
      user_requirement = [{
          "role": "user",
          "content":
          f"The user requirement: {user_msg}\n\
          The table_company table contains basic company information with columns: ['股號', '股名', '產業別', '股本', '市值']\n\
          The table_daily table is a daily stock price table with columns: ['股號', '日期', '開盤價', '最高價', '最低價', '收盤價', '還原價', '成交量', '殖利率', '日本益比', '股價淨值比', '三大法人買賣超股數', '融資買入', '融卷賣出']\n\
          The table_quarterly table is a quarterly revenue table with columns: ['股號', '日期', '營業收入', '營業費用', '稅後淨利', '每股盈餘']\n\
          Your task is to develop a Python function named 'calculate(table_company, table_daily, table_quarterly)'.Only using Pandas.Using the groupby() function in calculate() and return a new DataFrame table that includes a unique list of stocks.Please rely on table_company to consolidate the stock list and ensures that there are no NaN or Inf values."
      }]
  
      msg = [{
          "role": "system",
          "content": "As a stock selection strategy robot, your task is to generate Python code based on user requirements. The code should utilize three DataFrame tables for stock selection, namely table_company, table_daily, and table_quarterly. Please note that your response should solely consist of the code itself, and no additional information should be included. After processing, please return a new DataFrame table that includes a unique list of stocks and ensures that there are no NaN or Inf values."
      }, {
          "role": "user",
          "content": "The user requirement:請選出大市值股(前10%)且近期營收成長最高的10檔股票"
      }, {
          "role": "assistant",
          "content": f"{code_example}"
      }]
  
      msg += user_requirement
  
  
      reply_data = self.get_reply(msg)
      cleaned_code = reply_data.replace("```", "")
      cleaned_code = cleaned_code.replace("python", "")
      return user_requirement, cleaned_code
  
  def ai_debug(self, history, code_str ,error_msg):
        msg = [{
            "role": "system",
            "content":
            "You will act as a professional Python code generation robot. \
            I will send you the incorrect code and error message.\
            Please correct and return the fixed code. \n\
            Only using Pandas. \
            Please note that your response should solely \
            consist of the code itself, \
            and no additional information should be included."}]
        msg += history
        msg += [{
            "role": "assistant",
            "content":f"{code_str}"
        }, {
            "role": "user",
            "content": f"The error code:{code_str} \n\
            The error message:{error_msg} \n\
            Please reconfirm user requirements \n\
            Your task is to develop a Python function named \
            'calculate(table_company, table_daily, table_quarterly)', \
            Please only using the Pandas library. \
            Please note that your response should solely \
            consist of the code itself, \
            and no additional information should be included."
        }]
  
  
        reply_data = self.get_reply(msg)
        cleaned_code = reply_data.replace("```", "")
        cleaned_code = cleaned_code.replace("python", "")
        return cleaned_code 


  
  # 建立訊息指令(Prompt)
  def generate_content_msg(self, stock_id, name_df):
  
      stock_name = self.stock_info.get_stock_name(
          stock_id, name_df) if stock_id != "大盤" else stock_id
  
      price_data = self.stock_price(stock_id)
      news_data = self.stock_news(stock_name)
  
      content_msg = f'你現在是一位專業的證券分析師, '\
        '你會依據以下資料來進行分析並給出一份完整的分析報告:\n'
  
      content_msg += f'近期價格資訊:\n {price_data}\n'
  
      if stock_id != "大盤":
          stock_value_data = self.stock_fundamental(stock_id)
          content_msg += f'每季營收資訊：\n {stock_value_data}\n'
  
      content_msg += f'近期新聞資訊: \n {news_data}\n'
      content_msg += f'請給我{stock_name}近期的趨勢報告,請以詳細、'\
        '嚴謹及專業的角度撰寫此報告,並提及重要的數字, reply in 繁體中文'
  
      return content_msg

  # StockGPT
  def stock_gpt(self, stock_id):
      content_msg = self.generate_content_msg(stock_id, self.name_df)
      msg = [{
          "role": "system",
          "content": f"你現在是一位專業的證券分析師, 你會統整近期的股價漲幅"\
        "、基本面、新聞資訊等方面並進行分析, 然後生成一份專業的趨勢分析報告, tokens數量上限為1600"
      }, {
          "role": "user",
          "content": content_msg
      }]
  
      reply_data = self.get_reply(msg)
      
      return reply_data
