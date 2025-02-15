import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import os, time
from datetime import datetime, timedelta


class StockDB:
  def __init__(self, db_path='./stock.db', db_start_date='2015-01-01'):
    exist = os.path.exists(db_path) #是否已建立資料庫
    self.db_path = db_path
    self.db_start_date = db_start_date
    self.conn = sqlite3.connect(db_path)
    self.ids = None
    if not exist: #如果未建立資料庫
      print("建立資料庫：" + db_path)
      self.create_tables() # 建立資料表

  # 建立資料表(不存在時才會建立)
  def create_tables(self):
    # Daily 日頻資料表用 "股號+日期" 為主鍵
    # 若要改為自動編號的主鍵,可用：序號 INTEGER PRIMARY KEY AUTOINCREMENT,
    self.conn.execute('''
    CREATE TABLE IF NOT EXISTS 公司 (
        股號 TEXT PRIMARY KEY NOT NULL,
        股名 TEXT,
        產業別 TEXT,
        股本 INTEGER,
        市值 INTEGER
    )
    ''')

    self.conn.execute('''
    CREATE TABLE IF NOT EXISTS 日頻 (
        股號 TEXT,
        日期 TEXT,
        開盤價 REAL,最高價 REAL,最低價 REAL,
        收盤價 READ,還原價 READ,成交量 INTEGER,
        日報酬 REAL,殖利率 REAL,日本益比 REAL,
        股價淨值比 REAL,三大法人買賣超股數 REAL,
        融資買入 REAL,融卷賣出 REAL,
        PRIMARY KEY (股號, 日期)
    )
    ''')   # ↑以股號+日期為主鍵
    self.conn.execute('CREATE INDEX 日期索引 ON 日頻(日期)') #建日期索引


    self.conn.execute('''
    CREATE TABLE IF NOT EXISTS 季頻 (
        股號 TEXT,
        年份 TEXT ,
        季度 REAL,營業收入 REAL,
        營業費用 REAL,稅後淨利 REAL,
        每股盈餘 REAL,
        PRIMARY KEY (股號, 年份, 季度)
    )
    ''')

    self.conn.commit()

  # 更新股票資訊
  def renew(self, if_renew_qu = True):
    self.renew_company() # 公司的基本資訊
    self.renew_daily() # 更新日頻的基本資訊
    if if_renew_qu == True:
      self.renew_quarterly_frequency_basic() # 更新季頻的基本資訊


  # 顯示資料表的結構及索引資訊
  def info(self, table):
    cursor = self.conn.execute(f"PRAGMA table_info({table})")
    column_list = cursor.fetchall()
    print(f"\n【{table}】資料表的結構：")
    for column in column_list:
      print(column)

    cursor = self.conn.execute(f"PRAGMA index_list({table})")
    index_list = cursor.fetchall()
    print("\n索引資訊：")
    for index in index_list:
      print('-------------')
      print(index)
      index_name = index[1]
      cursor = self.conn.execute(f"PRAGMA index_info({index_name})")
      index_columns = cursor.fetchall()
      print('索引欄位：')
      for column in index_columns:
        print(column)

  # 讀取資料 (可有多個資料表, 以逗號分隔, 此時要加上 where 條件。
  #       若有同名欄位, 則要寫成 "資料表.欄位")
  # 參數 psdate (parse_date) 表示是否將日期欄的資料轉為日期型別,預設為 True
  # 傳回 DataFrame
  def get(self, table, select=None, where=None, psdate=False): #參數：資料表, 欄位, 條件式, 解析日期欄
    # 查詢資料
    if not isinstance(table, str): #如果不是字串, 就將元素以逗號組合
      table = ", ".join(table)

    if not select:
      select = "*"
    elif not isinstance(select, str): #如果不是字串, 就將元素以逗號組合
      select = ", ".join(select)


    sql = f"SELECT {select} FROM {table}"
    if where:
      sql += f" WHERE {where}"
    if psdate: # 要解析日期欄位, 將之轉為日期型別
      if table == '日頻':
        df = pd.read_sql(sql, self.conn, parse_dates=['日期'])
      elif table == '季頻':
        sql = '''
        SELECT 股號, 
            營業收入, 
            營業費用, 
            稅後淨利, 
            每股盈餘,
            strftime('%Y-%m-%d', 年份 || '-' || 
            CASE 
                WHEN 季度 = 'Q1' THEN '03' 
                WHEN 季度 = 'Q2' THEN '06'
                WHEN 季度 = 'Q3' THEN '09'
                WHEN 季度 = 'Q4' THEN '12'
            END || '-01') as 日期
            
        FROM 季頻
        ORDER BY 股號 ASC, 日期 DESC'''
        df = pd.read_sql(sql, self.conn, parse_dates=['日期']) 
        column_order = ['股號', '日期', '營業收入', '營業費用', '稅後淨利', '每股盈餘']
        df = df[column_order]
        
    else:
      df = pd.read_sql(sql, self.conn)
    return df

  # 關閉資料庫
  def close(self):
    self.conn.close()


  ##############################
  ## 更新股票資訊的相關方法 ##
  ##############################

  #讀取最近一天所有股票的日頻資料, 以取得最新的股號及股名清單
  #欄位："股號","股名","成交量","成交金額","開盤價","最高價","最低價","收盤價","漲跌價差","成交筆數"

  # 上市股票
  def stock_name(self):
    # print(self.ids)
    if self.ids is not None:
      return self.ids
    print("線上讀取股號、股名、及產業別")
    data=[]
    response=requests.get('https://isin.twse.com.tw/isin/C_public.jsp?strMode=2')
    url_data=BeautifulSoup(response.text, 'html.parser')
    stock_company=url_data.find_all('tr')
    for i in stock_company[2:]:
        j=i.find_all('td')
        l=j[0].text.split('\u3000')
        if len(l[0].strip()) == 4:
            stock_id,stock_name = l
            industry = j[4].text.strip()
            data.append([stock_id.strip(),stock_name,industry])
        else:
            break
    df = pd.DataFrame(data, columns=['股號','股名','產業別'])
    self.ids = df
    return df

  #更新公司基本資料, 預設只會加入新上市的公司, 若將參數all設為Ture則全部更新
  def renew_company(self, all=False):
    df_old = self.get("公司", '股號,股名,產業別')
    if all or df_old.empty: # 先刪除全部, 再重新讀取
      self.conn.execute("DELETE FROM 公司")
      df = self.stock_name()
      print('更新所有的公司：', df)
    else:
      df_new = self.stock_name()
      mask = df_new['股號'].isin(df_old['股號']) # 建立在new存在,在old也存在的遮罩
      df = df_new[~mask] #反轉遮罩, 取出在new有在old沒有的資料
      print('要更新的公司：', df)

    for id,name,industry in zip(df['股號'],df['股名'],df['產業別']):
      try:
        stock = yf.Ticker(id+".TW")
        if not 'sharesOutstanding' in stock.info:
          stock_sharesOutstanding = None
        else:
          stock_sharesOutstanding=stock.info['sharesOutstanding']
        if not 'marketCap' in stock.info:
          stock_marketCap = None
        else:
          stock_marketCap=stock.info['marketCap']
  
        self.conn.execute("INSERT INTO 公司 values(?,?,?,?,?)",
                  (id,name,industry,stock_sharesOutstanding,stock_marketCap))
        self.conn.commit()
        # print(id)
      except:
        pass

  def quarter_to_int(self, year, quarter):
    quarter_dict = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    return int(year) * 10 + quarter_dict[quarter]

  # 更新季頻的基本資訊
  def renew_quarterly_frequency_basic(self):
    #找出最後更新日期
    cursor = self.conn.execute('SELECT 年份, 季度 FROM 季頻 ORDER BY 年份 DESC, 季度 DESC LIMIT 1')
    m_date = cursor.fetchone()
    latest_year, latest_quarter = m_date
    print('季頻基本資料的最後更新日：', m_date)  #for debug
    today = datetime.now()
    q1_release = datetime(today.year, 5, 15)
    q2_release = datetime(today.year, 8, 14)
    q3_release = datetime(today.year, 11, 14)
    q4_release = datetime(today.year, 3, 31)
    if q1_release <= today < q2_release:
        report_type = "Q1"
    elif q2_release <= today < q3_release:
        report_type = "Q2"
    elif q3_release <= today <  datetime(today.year + 1, 3, 31) or datetime(today.year - 1, 11, 14) <= today < q4_release:
        report_type = "Q3"
    elif q4_release <= today < q1_release:
        report_type = "Q4"
    
    print(f"當前狀態: {report_type}")
    
    if report_type == latest_quarter:
      return print("不用更新")
    else:
      #更新季頻資料表
      print('更新季頻')
      
      df = self.stock_name()
      for id, name in zip(df['股號'],df['股名']):
          df_data=[]
          url = [f'https://tw.stock.yahoo.com/quote/{id}.TW/income-statement',
                  f'https://tw.stock.yahoo.com/quote/{id}.TW/eps']
          df = self.url_find(url[0])
          print(id)
          df = df.transpose()
          df.columns = df.iloc[0]
          df = df[1:]
          df.insert(0,'年度/季別',df.index)
          df.columns.name = None
          df.reset_index(drop=True, inplace=True)
          df_data.append(df)
  
          # 季EPS表
          df=self.url_find(url[1])
          df_data.append(df)
  
          # 將兩個 DataFrame 按列名合併
          combined_df = df_data[0].merge(df_data[1], on='年度/季別')
          # print 合併後的DataFrame
          combined_df=combined_df.iloc[:,[0,1,3,5,6]]
          combined_df[['年份', '季度']] = combined_df['年度/季別'].str.split(' ', expand=True)
          combined_df.drop(columns=['年度/季別'], inplace=True)
  
          # 重新排列列的顺序
          combined_df = combined_df[['年份', '季度', '營業收入', '營業費用', '稅後淨利', '每股盈餘']]
          combined_df.insert(0, '股號', id)   # 加入股號欄
          try:
            combined_df.to_sql('季頻', self.conn, if_exists='append', index=False)
          except:
              continue
      return print("更新完成")
   

  def url_find(self,url):
    words = url.split('/')
    k = words[-1]
    # 使用requests取得網頁內容
    response = requests.get(url)
    html = response.content

    # 使用Beautiful Soup解析HTML內容
    soup = BeautifulSoup(html, 'html.parser')

    # 找到表格的表頭
    table_soup = soup.find('section', {'id': 'qsp-{}-table'.format(k)})
    table_fields=table_soup.find('div', class_='table-header')

    table_fields_lines = list(table_fields.stripped_strings)
    data_rows = table_soup.find_all('li' ,class_='List(n)')

    # 解析資料行內容
    data = []
    for row in data_rows:
        row_data = list(row.stripped_strings)
        # row_data[1:] = [item.replace(',', '') for item in row_data[1:]]
        row_data[1] = row_data[1].replace(',', '')
        data.append(row_data[0:2])

    # 建立 DataFrame
    df = pd.DataFrame(data, columns=table_fields_lines[0:2])
    return df

  # 日頻股價資料
  def stock_price(self, stock_list, start_date):
    # 下載資料
    df = yf.download(stock_list, start_date)

    if len(df) > 0: # 如果有下載到資料
        # 轉換資料
        data_list = []
        for stock in stock_list:
            stock_df = df.xs(stock, axis=1, level=1).copy()
            stock_df['Stock_Id'] = stock.replace('.TW', '')
            data_list.append(stock_df)

        yf_df = pd.concat(data_list).reset_index()

        # 重新排列欄位
        yf_df = yf_df[['Date', 'Stock_Id', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        yf_df.rename(columns={  # 修改欄位名稱以便對應到資料表
            'Stock_Id':'股號','Date':'日期','Open':'開盤價','High':'最高價','Low':'最低價',
            'Close':'收盤價', 'Adj Close':'還原價','Volume':'成交量',}, inplace=True)
        # ↓將TimeStamp資料改為如 "2022-02-03" 的字串
        yf_df['日期'] = yf_df['日期'].dt.strftime('%Y-%m-%d')

        return yf_df

  # 進階日頻資料下載
  def stock_advanced(self, date):
      urls = [
          f"https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?date={date}&selectType=ALL&response=json",
          f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date}&selectType=ALLBUT0999&response=json",
          f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={date}&selectType=STOCK&response=json"
      ]
      # 取得本益比資料
      json_data1=requests.get(urls[0]).json()
      # 有資料才執行程式
      if 'stat' in json_data1 and json_data1['stat'] == 'OK':
          df1 = pd.DataFrame(json_data1['data'], columns=json_data1['fields'])
          df1 = df1[['證券代號','殖利率(%)','本益比','股價淨值比']]
          df1.insert(1, '日期', datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'))
          df1.rename(columns={
                  '證券代號':'股號','殖利率(%)':'殖利率','本益比':'日本益比'
                  }, inplace=True)
      time.sleep(2)
      # 取得法人買賣超資料
      json_data2=requests.get(urls[1]).json()
      if 'stat' in json_data2 and json_data2['stat'] == 'OK':
          df2 = pd.DataFrame(json_data2['data'], columns=json_data2['fields'])
          df2 = df2[['證券代號','三大法人買賣超股數']]
          df2.rename(columns={
                  '證券代號':'股號'
                  }, inplace=True)
      time.sleep(2)
      # 取得融資融券資料
      json_data3=requests.get(urls[2]).json()
      if 'stat' in json_data3 and json_data3['stat'] == 'OK':
          data = pd.DataFrame(json_data3['tables'][1]['data'])
          df3 = data.iloc[:, [0, 2, 9]]
          df3.columns = ['股號', '融資買入', '融卷賣出']
      time.sleep(2)

      try:
        merged_df = df1.merge(df2, on='股號', how='inner')
        merged_df = merged_df.merge(df3, on='股號', how='inner')
        time.sleep(2)
        return merged_df
      except Exception as e:
        print(f"Error during merging dataframes: {e}")
        return pd.DataFrame()

  # 更新日頻的基本資訊
  def renew_daily(self):
    #找出最後更新日期
    cursor = self.conn.execute('SELECT MAX(日期) FROM 日頻 WHERE 開盤價 IS NOT NULL')
    m_date = cursor.fetchone()[0]
    print('日頻基本資料的最後更新日：', m_date)  #for debug
    if not m_date:
      start_date = self.db_start_date  #抓全部
    else:
      input_date = datetime.strptime(m_date, '%Y-%m-%d') # 將字串轉換為日期型別
      next_day = input_date + timedelta(days=1) # 將日期加一天
      today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
      if next_day >= today: #如果不用更新
        print("不用更新！")
        return
      start_date = next_day.strftime('%Y-%m-%d') # 格式化日期為 "2020-02-23" 格式的字串

    print("開始日期：", start_date)
    # 要更新的股票代碼
    stock_list = (self.stock_name()['股號'] + '.TW').tolist()

    # 先取得股價資料
    base_df = self.stock_price(stock_list, start_date)
    # 交易日期
    date_list = base_df['日期'].str.replace('-', '')
    date_list = date_list.unique().tolist()
    date_list.pop()
    # 證交所資料更新
    print("更新日本益比、融資融卷、三大法人資料")
    if len(date_list) == 0:
      print('不用更新!')
      return
    advance_df = pd.DataFrame()
    for date in date_list:
      print("完成更新:", date)
      df = self.stock_advanced(date)
      advance_df = pd.concat([advance_df,df])

    # 所有表格
    final_df = pd.merge(base_df, advance_df, on=['日期', '股號'], how='inner')
    print(final_df)
    final_df.to_sql('日頻', self.conn, if_exists='append', index=False)


  # 顯示所有資料表的結構及索引資訊
  def table_info(self):
    t_list = {}
    # 取得所有資料表的名稱
    cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = cursor.fetchall()

    print("●顯示所有資料表的結構及索引資訊")
    print("=" * 40)
    for table in table_names:
      table_name = table[0]
      print(f"資料表：{table_name}\n")
      
      # 取得資料表的欄位資訊
      cursor.execute(f"PRAGMA table_info({table_name});")
      columns = cursor.fetchall()
      column_names = [] # 用來儲存當前表的所有欄位名
      for column in columns:
        if column[5] == 0:
          column_names.append(column[1])
          print(f"欄位：{column[1]}, {column[2]}")
        else:
          column_names.append(column[1])
          print(f"欄位：{column[1]}, {column[2]}, 主键：{column[5]}")

      # 取得資料表的索引資訊
      cursor.execute(f"PRAGMA index_list({table_name});")
      indexes = cursor.fetchall()
      for index in indexes:
          index_name = index[1]
          is_unique = "唯一" if index[2] else "非唯一"
          print(f"索引：{index_name}, 類型：{is_unique}")
      t_list[table_name] = column_names
      print("=" * 40)
    return t_list

  # 檢查所有資料表的資料範圍及空值狀況
  # 可用 table_list 指定要check哪些table, 以序號(0~4)指定, 例如 [1,3,4]
  def table_check(self, table_list=None):
    table = ('公司','日頻','季頻')
    table_msg = ('公司(記錄數, 股號數)',
           '日頻(記錄數, 股號數, 由, 到)',
           '季頻(記錄數, 股號數, 由, 到)')
    query = (
      ('''SELECT
        COUNT(*) AS 記錄數, COUNT(DISTINCT 股號) AS 股號數
        FROM 公司'''),
      ('''SELECT
        COUNT(*) AS 記錄數, COUNT(DISTINCT 股號) AS 股號數,
        MIN(日期) AS 由, MAX(日期) AS 到
        FROM 日頻'''),
      ('''SELECT
        COUNT(*) AS 記錄數, COUNT(DISTINCT 股號) AS 股號數,
        MIN(年份) AS 由, MAX(年份) AS 到
        FROM 季頻'''))
    print("●檢查所有資料表的資料筆數、日期範圍、及空值狀況")
    if table_list is None:
      table_list = range(3)
    for i in table_list:
      # 顯示資料筆數及日期範圍
      print("=" * 40)
      cursor = self.conn.execute(query[i])
      result = cursor.fetchone()
      print(f"○{table_msg[i]}")
      print(result)

    print("=" * 40)
