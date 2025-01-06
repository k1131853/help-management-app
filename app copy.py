import streamlit as st
from datetime import date
import gspread
import os
import json
import pandas as pd

# シークレット情報を読み込む
service_account = st.secrets["service_account"]
google_sheet_url = st.secrets["google_sheet"]["url"]

# Google Service Accountを設定
gc = gspread.service_account_from_dict(service_account)
# Google Sheetsを開く
sh = gc.open_by_key(google_sheet_url)

#本日の日付を取得
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
st.markdown(
    f"""
    <div style="font-size:24px;">
     ユーザーは<span style="color:red;,fontsize:30px;font-weight:bold;">{user}</span>です!!
     </div>
     """,
     unsafe_allow_html=True
)
st.write("※ユーザー変更の際はサイドバーより変更してください")

if user == "ママ":
    st.image("photo/IMG_2755.JPG")
    money_col = 2
elif user == "あーちゃん":
    st.image("photo/IMG_5197.JPG")
    money_col = 3
elif user == "パパ":
    st.image("photo/IMG_5219.JPG")
    money_col = 4
else:
    st.write("画像の読み込みに失敗しました")

st.markdown(
    f"""
    <div style="font-size:24px;">
        <span>&lt;お手伝い内容&gt;</span>&nbsp;&nbsp;&nbsp;{formatted_date}
    </div>
    """,
    unsafe_allow_html=True
)
sh = sh.worksheet("集計表")

def check_value(formatted_date):
    cell = sh.find(formatted_date)
    if cell:
        new_row = cell.row
        money = sh.cell(new_row, money_col).value or 0
        return new_row, int(money)
    new_row = len(sh.col_values(1)) + 1  # A列を取得して次の行番号を計算
    return new_row, 0


otetudai_dict = {"sentaku":161,"syokusenki":26,"kitchen":107,"huro":215,"senmendai":80,"ruro":134,"gomi_matome":53,"gomi_dashi":188}

checkbox_keys = {
    "sentaku": "洗濯機起動:161円", "syokusenki": "食洗機運転:26円", 
    "kitchen": "キッチンリセット:107円", "huro": "風呂掃除:215円", 
    "senmendai": "洗面台リセット:80円", "ruro": "掃除機またはルーロ起動:134円", 
    "gomi_matome": "ゴミまとめ:53円", "gomi_dashi": "ゴミ出し:188円"
}

checkbox_states = {key: st.checkbox(label, key=key) for key, label in checkbox_keys.items()}

new_row, money = check_value(formatted_date=formatted_date)

def handle_task_button(checkbox_states, sh, new_row, money):
    for idx, (key, checked) in enumerate(checkbox_states.items(), start=5):
        if checked:
            already_done = sh.cell(new_row, idx).value == "1"
            if not already_done:
                money += otetudai_dict[key]
                sh.update_cell(new_row, idx, 1)
            else:
                st.write(f"既に{checkbox_keys[key]}はやっています。")
    if money > 0:
        st.write(f"{money}円ゲットしました")
        sh.update_cell(new_row, money_col, money)
    else:
        st.write("チェックされていないか既に実施しています。")

if st.button("やりました"):
    handle_task_button(checkbox_states, sh, new_row, money)


def df_create(sh,today):
    df = pd.DataFrame(sh.get_all_values())
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.loc[:,~df.columns.str.isdigit()]
    df["日付"] = pd.to_datetime(df["日付"],format="%Y年%m月%d日")
    df.set_index("日付",inplace=True)
    y_date = int(today.strftime("%Y"))
    m_date = int(today.strftime("%m"))
    d_date = int(today.strftime("%d"))
    df = df[df.index.year == y_date]
    df = df[df.index.month == m_date]
    df = df.apply(pd.to_numeric) #数値に変換する
    df = df.fillna(0)
    mama_money = int(df["ママ金額"].sum())
    a_money =  int(df["あーちゃん金額"].sum())
    papa_money = int(df["パパ金額"].sum())
    today_df = df[df.index.day == d_date]
    today_df = today_df.iloc[:,3:]
    plot_df = df.iloc[:,:3]
    return mama_money,a_money,papa_money,today_df,plot_df

mama_money,a_money,papa_money,today_df,plot_df = df_create(sh,today)
if user == "ママ":
    total_money = mama_money
elif user == "あーちゃん":
    total_money = a_money
elif user == "パパ":
    total_money = papa_money

st.markdown(
    f"""
    <div style="font-size:24px;">
    <span>&lt;今月の獲得金額&gt;</span>&nbsp;&nbsp;&nbsp;<span style="color:red;fontsize:30px;font-weight:bold;">{total_money}円</span>
    </div>
    """,
    unsafe_allow_html=True)
st.write("")

st.subheader("獲得金額の推移")
st.line_chart(data=plot_df,width=0,height=0,use_container_width=True)

if st.button("まだやっていないものを確認"):
    count = 0
    for col in today_df.columns:
        if (today_df[col] != 1).any():  # 1でない値が一つでもあればTrue
            st.write("・",col)
            count +=1
        elif count == 8:
            st.write("ありません")