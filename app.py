import streamlit as st
from datetime import date,timedelta,datetime
import gspread
import os
import json
import pandas as pd
from google.oauth2 import service_account
from dateutil.relativedelta import relativedelta
import pytz
import time

st.set_page_config(layout="wide")

@st.cache_resource
def acsess_gc():
    scopes = [ 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info( st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(credentials)
    # スプレッドシートからデータ取得
    SP_SHEET_KEY = st.secrets.SP_SHEET_KEY.key # スプレッドシートのキー
    sh = gc.open_by_key(SP_SHEET_KEY)
    sh = sh.worksheet("集計表")
    return sh

def df_create(sh,today):
    df = pd.DataFrame(sh.get_all_values())
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.loc[:,~df.columns.str.isdigit()]
    df["日付"] = pd.to_datetime(df["日付"],format="%Y年%m月%d日")
    df.set_index("日付",inplace=True)
    #今月の金額を取得
    y_date = int(today.strftime("%Y"))
    m_date = int(today.strftime("%m"))
    d_date = int(today.strftime("%d"))
    df_1 = df[df.index.year == y_date]
    df_1 = df_1[df_1.index.month == m_date]
    df_1 = df_1.apply(pd.to_numeric) #数値に変換する
    df_1 = df_1.fillna(0)
    mama_money = int(df_1["ママ金額"].sum())
    a_money =  int(df_1["あーちゃん金額"].sum())
    papa_money = int(df_1["パパ金額"].sum())
    #本日の家事を取得
    today_df = df_1[df_1.index.day == d_date]
    today_df = today_df.iloc[:,3:]
    plot_df = df_1.iloc[:,:3]
    #先月の金額を取得
    last_month = today - relativedelta(months=1)
    last_y_date = int(last_month.strftime("%Y"))
    last_m_date = int(last_month.strftime("%m"))
    df_2 = df[df.index.year == last_y_date]
    df_2 = df_2[df_2.index.month == last_m_date]
    df_2 = df_2.apply(pd.to_numeric) #数値に変換する
    df_2 = df_2.fillna(0)
    mama_money_2 = int(df_2["ママ金額"].sum())
    a_money_2 =  int(df_2["あーちゃん金額"].sum())
    papa_money_2 = int(df_2["パパ金額"].sum())



    return mama_money,a_money,papa_money,today_df,plot_df,mama_money_2,a_money_2,papa_money_2

def check_value(formatted_date):
    cell = sh.find(formatted_date)
    if cell:
        new_row = cell.row
        money = sh.cell(new_row, money_col).value or 0
        return new_row, int(money),False
    new_row = len(sh.col_values(1)) + 1  # A列を取得して次の行番号を計算
    return new_row, 0,True

def handle_task_button(checkbox_states, sh, new_row, money):
    get_money = 0
    for idx, (key, checked) in enumerate(checkbox_states.items(), start=5):
        if checked:
            already_done = sh.cell(new_row, idx).value == "1" or sh.cell(new_row, idx).value == "2" or sh.cell(new_row, idx).value == "3"
            if not already_done:
                get_money += otetudai_dict[key]
                sh.update_cell(new_row,1,formatted_date) #日付入力
                sh.update_cell(new_row, idx, money_col-1) #やっているものに1を入力
            else:
                    if sh.cell(new_row, idx).value == "1":
                        st.write(f"{checkbox_keys[key]}はママがやっています。")
                    elif sh.cell(new_row, idx).value == "2":
                        st.write(f"{checkbox_keys[key]}はあーちゃんがやっています。")
                    elif sh.cell(new_row, idx).value == "3":
                        st.write(f"{checkbox_keys[key]}はパパがやっています。")
    if get_money > 0:
        st.success(f"{get_money}円ゲットしました")
        sh.update_cell(new_row, money_col, money+get_money)
    else:
        st.error("チェックされていないか既に実施しています。")

# ボタン押下時のセッション状態の初期化
if "clicked" not in st.session_state:
    st.session_state.clicked = False
# ボタン押下時の演出
def run_action():
    st.session_state.clicked = True

id_auth = st.text_input("IDを入力してください")
id_check = st.secrets.check_id.id

# 初回認証
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False  # 初期値は False

if st.button("確定", key="id_check"):
    if id_auth != id_check:
        st.info("認証されませんでした")
        st.session_state.authenticated = False
    else:
        st.session_state.authenticated = True  # 認証成功を記録

# 認証が完了している場合のみアプリを表示
if st.session_state.authenticated:
    sh = acsess_gc()

    #本日の日付を取得
    japan_tz = pytz.timezone('Asia/Tokyo')
    today = date.today()
    formatted_date = today.strftime("%Y年%m月%d日")

    st.title("💰️お手伝い管理アプリ💰️")
    st.markdown(
        """
        <div style="font-size:24px;">
        報酬は<span style="fontsize:28px;,font-weight:bold;">*毎月1日*</span>に支払われます。
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.write("ユーザー変更")
        user = st.sidebar.selectbox("選択してください",["ママ","あーちゃん","パパ"])

    st.write("※ユーザー変更はサイドバーより変更してください")



    mama_money,a_money,papa_money,today_df,plot_df,mama_money_2,a_money_2,papa_money_2 = df_create(sh,today)



    if user == "ママ":
        st.image("photo/IMG_2755.JPG")
        money_col = 2
        total_money = mama_money
        last_money = mama_money_2
    elif user == "あーちゃん":
        st.image("photo/IMG_5197.JPG")
        money_col = 3
        total_money = a_money
        last_money = a_money_2
    elif user == "パパ":
        st.image("photo/IMG_5219.JPG")
        money_col = 4
        total_money = papa_money
        last_money = papa_money_2
    else:
        st.error("画像の読み込みに失敗しました")

    st.markdown(
        f"""
        <div style="font-size:24px;">
        ユーザーは<span style="color:red;,fontsize:30px;font-weight:bold;">{user}</span>です!!
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="font-size:24px;">
            <span>&lt;お手伝い内容&gt;</span>&nbsp;&nbsp;&nbsp;{formatted_date}
        </div>
        """,
        unsafe_allow_html=True
    )



    otetudai_dict = {"sentaku":110,"syokusenki":17,"kitchen":105,"huro":228,"senmendai":52,"ruro":100,"gomi_matome":35,"gomi_dashi":158,"sentaku_matome":87,"syokki":70}

    checkbox_keys = {
        "sentaku": "洗濯機起動:110円", "syokusenki": "食洗機運転:17円", 
        "kitchen": "キッチンリセット:105円", "huro": "風呂掃除:228円", 
        "senmendai": "洗面台リセット:52円", "ruro": "掃除機またはルーロ起動:100円", 
        "gomi_matome": "ゴミまとめ:35円", "gomi_dashi": "ゴミ出し:158円",
        "sentaku_matome":"洗濯物畳む:87円","syokki":"食器出し＆ゴミ取り:70円"
    }
    new_row, money,new_result = check_value(formatted_date=formatted_date)

    checkbox_states = {key: st.checkbox(label, key=key) for key, label in checkbox_keys.items()}

    st.button("やりました！", on_click=run_action)

    if st.session_state.clicked:
        st.info("処理を開始します...")
        handle_task_button(checkbox_states, sh, new_row, money)
        time.sleep(1)
        st.balloons()  # 風船アニメーション
        st.session_state.clicked = False


    st.markdown(
        f"""
        <div style="font-size:24px;">
        <span>&lt;今月の獲得金額&gt;</span>&nbsp;&nbsp;&nbsp;<span style="color:red;fontsize:30px;font-weight:bold;">{total_money}円</span>
        </div>
        """,
        unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="font-size:24px;">
        <span>&lt;先月の獲得金額&gt;</span>&nbsp;&nbsp;&nbsp;<span style="color:blue;fontsize:30px;font-weight:bold;">{last_money}円</span>
        </div>
        """,
        unsafe_allow_html=True)


    st.subheader("獲得金額の推移")
    st.line_chart(data=plot_df,width=0,height=0,use_container_width=True,color=["#fd0", "#98FB98", "#00FFFF"])



    if st.button("まだやっていないものを確認"):
        count = 0
        if new_result:
            st.error("全てやっていません。")
        else:
            for col in today_df.columns:
                if not today_df[col].isin([1, 2, 3]).all():
                    st.write("・",col)
                else:
                    count +=1
        
            if count == 10:
                st.success("全て実施しています")

else:
    st.warning("認証が必要です。IDを入力してください。")