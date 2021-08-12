import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests as r
import regex as re
from dateutil import parser
import streamlit as st

def date_time_parser(dt):
    return int(np.round((dt.now(dt.tz) - dt).total_seconds() / 60, 0))

def elapsed_time_str(mins):
    time_str = ''
    hours = int(mins / 60)
    days = np.round(mins / (60 * 24), 1)
    remaining_mins = int(mins - (hours * 60))
    if (days >= 1):
        time_str = f'{str(days)} days ago'
        if days == 1:
            time_str = 'a day ago'
    elif (days < 1) & (hours < 24) & (mins >= 60):
        time_str = f'{str(hours)} hours and {str(remaining_mins)} mins ago'
        if (hours == 1) & (remaining_mins > 1):
            time_str = f'an hour and {str(remaining_mins)} mins ago'
        if (hours == 1) & (remaining_mins == 1):
            time_str = f'an hour and a min ago'
        if (hours > 1) & (remaining_mins == 1):
            time_str = f'{str(hours)} hours and a min ago'
        if (hours > 1) & (remaining_mins == 0):
            time_str = f'{str(hours)} hours ago'
        if ((mins / 60) == 1) & (remaining_mins == 0):
            time_str = 'an hour ago'
    elif (days < 1) & (hours < 24) & (mins == 0):
        time_str = 'Just in'
    else:
        time_str = f'{str(mins)} minutes ago'
        if mins == 1:
            time_str = 'a minute ago'
    return time_str
        

def rss_parser(i):
    b1 = BeautifulSoup(str(i),"xml")
    title = b1.find("title").get_text()
    url = b1.find("link").get_text()
    desc = b1.find("description").get_text()
    desc = desc.replace("&lt;", "<")
    desc = desc.replace("&gt;", ">")
    desc = re.sub("<.*?>", "", desc)
    desc = desc[:500] if len(desc) >= 500 else desc
    date = b1.find("pubDate").get_text()
    if url.find("businesstoday.in") >=0:
        date = date.replace("GMT", "+0530")
    date1 = parser.parse(date)
    return pd.DataFrame({"title": title,
                        "url": url,
                        "description": desc,
                        "date": date,
                        "parsed_date": date1}, index=[0])

rss = ['https://www.economictimes.indiatimes.com/rssfeedstopstories.cms',
       'http://feeds.feedburner.com/ndtvprofit-latest?format=xml',
      'https://www.thehindubusinessline.com/news/feeder/default.rss',
      'https://www.moneycontrol.com/rss/latestnews.xml',
      'https://www.livemint.com/rss/news',
      'https://www.financialexpress.com/feed/',
      'https://www.business-standard.com/rss/latest.rss',
      'https://www.businesstoday.in/rssfeeds/?id=225346',
      'https://www.zeebiz.com/latest.xml/feed']

def src_parse(rss):
    if rss.find('ndtvprofit') >= 0:
        rss = 'ndtv profit'
    rss = rss.replace("https://www.", "")
    rss = rss.split("/")
    return rss[0]
    
    
def news_agg(rss):
    rss_df = pd.DataFrame()
    resp = r.get(rss, headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"})
    b = BeautifulSoup(resp.content, "xml")
    items = b.find_all("item")
    for i in items:
        rss_df = rss_df.append(rss_parser(i)).copy()
    rss_df["description"] = rss_df["description"].replace([" NULL", ''], np.nan)
    rss_df.dropna(inplace=True)
    rss_df["src"] = src_parse(rss)
    rss_df["elapsed_time"] = rss_df["parsed_date"].apply(date_time_parser)
    rss_df["elapsed_time_str"] = rss_df["elapsed_time"].apply(elapsed_time_str)
    return rss_df


final_df = pd.DataFrame()
for i in rss:
    final_df = final_df.append(news_agg(i))

final_df.sort_values(by="elapsed_time", inplace=True)
final_df['src_time'] = final_df['src'] + ("&nbsp;"*5) + final_df["elapsed_time_str"]
final_df.drop(columns=['date', 'parsed_date', 'src', 'elapsed_time', 'elapsed_time_str'], inplace=True)
final_df.drop_duplicates(subset='description', inplace=True)
    
result_str = '<html><table style="border: none;">'
for n, i in final_df.iterrows(): #iterating through the search results
    href = i["url"]
    description = i["description"]
    url_txt = i["title"]
    src_time = i["src_time"]
    result_str += f'<tr style="border: none; font-weight: bold; font-size: 23px; background-color: whitesmoke;"><a href="{href}" target="_blank">{url_txt}</a></tr>'+\
    f'<tr style="border: none; background-color: whitesmoke;">{description}</tr>'+\
    f'<tr style="border: none; color: green; font-size: 14px; font-weight: bold; background-color: whitesmoke;">{src_time}</tr>'+\
    f'<tr style="border: none;"><td style="border: none; height: 30px;"></td></tr>'

result_str += '</table></html>'

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.markdown(f'<h1 style="background-color: gainsboro; padding-left: 10px; padding-bottom: 20px;">News Aggregator</h1><h5>* Aggregates news from the RSS feeds of top Indian business news websites</h5><br>', unsafe_allow_html=True)
st.markdown(result_str, unsafe_allow_html=True)
