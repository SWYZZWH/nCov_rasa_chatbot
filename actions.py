# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/


# This is a simple example for a custom action which utters "Hello World!"
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from typing import Dict, Text, Any, List

import requests
from rasa_sdk import Action
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.forms import FormAction
from rasa.core import actions
from rasa.core import events
from rasa.core.events import (
    UserUtteranceReverted,
    UserUttered,
    ActionExecuted,
    Event,
    BotUttered,
)

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time

base_url = "https://lab.isaaclin.cn/nCoV/api/"

api_patterns = {
    "overall":["latest"],
    "provinceName":[],
    "area":["latest","province"],
    "news":["province","num"],
    "rumors":["rumorType","num"]
}

response_templates = {
    "overall":"全国疫情情况:\n现存确诊人数:{}\n累计确诊人数:{}\n疑似病例:{}\n累计治愈:{}\n死亡人数:{}",
    "area":"{}疫情情况:\n现存确诊人数:{}\n累计确诊人数:{}\n疑似病例:{}\n累计治愈:{}\n死亡人数:{}",
    "news":"{}最新新闻:\n",
    "rumors":"最新谣言与辟谣:\n"
}

def create_url(api_pattern,paras,base = "https://lab.isaaclin.cn/nCoV/api/"):
    url = base
    if api_pattern in api_patterns.keys():
        url += api_pattern
        
    if paras:
        url += "?"
        
    url += "&".join([key+"="+value for key,value in paras.items()])
    return url



class ActionSearchOverall(Action):
    def name(self) -> Text:
        return "action_search_overall"
        
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        
        location = tracker.get_slot("location").strip(" ")
        paras = {}
        if location != "全国":
            api_pattern = "area"
            paras["province"] = location
        else:
            api_pattern = "overall"
        #latest = 1
        #paras["latest"] = latest
        
        
        #grab all information first,then filter
        full_url = create_url(api_pattern,paras)
        ret = requests.get(full_url).json()
        print(full_url)
        print(ret)
        
        response_paras = []
        if not ret.get("results") or ret.get("success") != True:
            dispatcher.utter_message(text="错误！")
            #return [SlotSet("numbers","null")]
            return
        else:
            #extract infos according to search mode
            results = ret["results"]
            
            if api_pattern == "area":
                #search location
                for loc in results:
                    if loc["provinceName"] == location or loc["provinceShortName"] == location:
                        loc_match = loc 
                        break
                    elif loc["cities"]:
                        for city in loc["cities"]:
                            if city["cityName"] == location:
                                loc_match = city
                                break
                if not loc_match:
                    dispatcher.utter_message(text="未找到该地区的信息！")
                    #return [SlotSet("overall_info","null")] 
                    return
                            
                response_paras.append(location)
            else:
                loc_match = results[0]
            print(loc_match)
                
            #print results
            
            response_paras += [loc_match["currentConfirmedCount"],loc_match["confirmedCount"],loc_match["suspectedCount"],\
                                  loc_match["curedCount"],loc_match["deadCount"]]
            
            response_text = response_templates[api_pattern].format(*response_paras)
                  
        dispatcher.utter_message(text=response_text)
        #return [SlotSet("numbers",response_text)]
        return


  
class ActionSearchNews(Action):
    def name(self) -> Text:
        return "action_search_news"
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        location = tracker.get_slot("location").strip(" ")
        num = 5 #can be adjusted by user
        paras = {}
        api_pattern = "news"
        
        if not location or location == "全国":
            #by default we get international news here although location is "中国"
            paras["num"] = "{}".format(num)
        else:
            paras["num"] = "all"
            
        
        #grab all information first,then filter
        full_url = create_url(api_pattern,paras)
        ret = requests.get(full_url).json()
        
        print(full_url)
        print(ret)
        
        #response_paras = []
        if not ret.get("results"):
            dispatcher.utter_message(text="不好意思，我没能找到相关的新闻！")
            #return [SlotSet("numbers","null")]
            return
        else:
            #wait to support keyword search function
            related_news = [] 
            if not location or location == "全国":
                related_news = ret["results"]
                response_text = response_templates[api_pattern].format("")
            else:
                related_news = [news for news in ret["results"] if news["provinceName"] == location]
                related_news = related_news[:num] #show up to num=5 pieces of news
                response_text = response_templates[api_pattern].format(location)
                
            #construct news information
            for news in related_news:                        
                response_text += "新闻标题："+ news["title"] + "\n" 
                response_text += "发布时间："+ time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(news["pubDate"]/1000)) +"\n"
                response_text += "来源链接："+ news["sourceUrl"] + "\n"
                #wait to add more infomation of news
                
        dispatcher.utter_message(text=response_text)
        #return [SlotSet("numbers",response_text)]
        return
    
    
class ActionSearchRumors(Action):
    def name(self) -> Text:
        return "action_search_rumors"
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        paras = {}
        paras["num"] = "5" #api default is 10;should be able to change according to users' need
        api_pattern = "rumors"
        
        #get all information
        full_url = create_url(api_pattern,paras)
        ret = requests.get(full_url).json()
        
        print(full_url)
        print(ret)
        
        response_paras = []
        if not ret.get("results"):
            dispatcher.utter_message(text="错误！")
            #return [SlotSet("numbers","null")]
            return
        else:
            #support keyword search function
            results = ret["results"]
            response_text = response_templates[api_pattern]
            for rumor in results:                        
                response_text += "谣言内容："+ rumor["title"] + "\n" 
                response_text += "辟谣内容："+ rumor["mainSummary"]+ "\n"
                # add more infomation of news
                
        dispatcher.utter_message(text=response_text)
        #return [SlotSet("numbers",response_text)]
        return
        
def draw_pic(save_path,title,x,x_label,y,y_label,y_dscr,z = None,z_dscr = None,d = None,d_dscr=None,c = None, c_dscr = None,legend = 'upper right'):
    # 设置画布大小
    plt.rcParams['savefig.dpi'] = 2000 #图片像素
    plt.rcParams['figure.dpi'] = 1500 #分辨率
    plt.figure(figsize=(40, 2))
    
    #tick_spacing = 1
    fig, ax = plt.subplots(1, 1)
    #ax.xaxis.set_major_locator(ticker.MaxNLocator(tick_spacing))

    # 标题
    plt.title(title)
    # 横坐标描述
    plt.xlabel(x_label)
    # 纵坐标描述
    plt.ylabel(y_label)

    # 这里设置线宽、线型、线条颜色、点大小等参数 并为每个数据点加标签
    ax.plot(x, y, label=y_dscr, linewidth=1, color='#0ebb67', marker='o', markerfacecolor='#0ebb67', markersize=2)
    for a, b in zip(x, y):
        plt.text(a, b, str(b), ha='center', va='bottom', fontsize=5)
    if z:
        ax.plot(x, z, label=z_dscr, linewidth=1, color='#2e9bed', marker='o', markerfacecolor='#2e9bed', markersize=2)
        for a, b in zip(x, z):
            plt.text(a, b, str(b), ha='center', va='bottom', fontsize=5)
    if d:
        ax.plot(x, d, label=d_dscr, linewidth=1, color='#3050ef', marker='o', markerfacecolor='#3050ef', markersize=2)
        for a, b in zip(x, d):
            plt.text(a, b, str(b), ha='center', va='bottom', fontsize=5)
    if c:
        ax.plot(x, c, label=c_dscr, linewidth=1, color='#fc921c', marker='o', markerfacecolor='#fc921c', markersize=2)
        for a, b in zip(x, c):
            plt.text(a, b, str(b), ha='center', va='bottom', fontsize=5)
                
    # 旋转x轴标签
    for label in ax.get_xticklabels():
        label.set_rotation(30)  # 旋转30度
        label.set_horizontalalignment('right')  # 向右旋转
        
    #显示中文
    plt.rcParams['font.sans-serif']='SimHei'
    plt.rcParams['axes.unicode_minus']=False

    # 图例显示及位置确定
    plt.legend(loc=legend)
    plt.rcParams['savefig.dpi'] = 2000 #图片像素
    plt.rcParams['figure.dpi'] = 1500 #分辨率
    plt.savefig(save_path, bbox_inches='tight')
    

    
class ActionDrawPics(Action):
    def name(self) -> Text:
        return "action_draw_pics"
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        #ret = requests.get("http://wuliang.art/ncov/dnalysis/ncovMaps").json()
        
        #if not ret.get("message") or ret["message"] != "SUCCESS":
        #    dispatcher.utter_message(text="错误！")
        #    return
        #else:
        #    #extract ness infos and draw pictures
        #    chart = ret["data"]["chartsTree"]
        #    x1_axis = [ data_info["date"] for data_info in chart[0]["datas"]][-14:]
        #    y1_axis = [ int(data_info["newconfirm"]) for data_info in chart[0]["datas"]][-14:] #新增确诊
        #    z1_axis = [ int(data_info["newsuspect"]) for data_info in chart[0]["datas"]][-14:] #新增疑似
        #    save_path1 = r"C:\Users\84353\chatbox\nCov_chatbox\test1.png"
        #    draw_pic(save_path1,chart[0]["name"],x1_axis,"日期",y1_axis,"人数","新增确诊",z1_axis,"新增疑似")

        #    x1_axis = [ data_info["date"] for data_info in chart[1]["datas"]][-14:]
        #    d1_axis = [ int(data_info["dead"]) for data_info in chart[1]["datas"]][-14:] #死亡
        #    c1_axis = [ int(data_info["heal"]) for data_info in chart[1]["datas"]][-14:] #治愈
        #    save_path2 = r"C:\Users\84353\chatbox\nCov_chatbox\test2.png"
        #    draw_pic(save_path2,chart[1]["name"],x1_axis,"日期",d1_axis,"人数","累计死亡",c1_axis,"累计治愈",legend="upper left")
            
        #show a picture
        #dispatcher.utter_message(image = "https://i.imgur.com/nGF1K8f.jpg")
        dispatcher.utter_message(text = "图片链接：https://wx2.sinaimg.cn/mw690/006Bji4dly1gcdluju1ggj314p0u0npd.jpg",image = "https://wx2.sinaimg.cn/mw690/006Bji4dly1gcdluju1ggj314p0u0npd.jpg")
        dispatcher.utter_message(text = "图片链接：https://wx4.sinaimg.cn/mw690/006Bji4dly1gcdlujv5j1j31580u0kjl.jpg",image = "https://wx4.sinaimg.cn/mw690/006Bji4dly1gcdlujv5j1j31580u0kjl.jpg")
        #dispatcher.utter_message(image = "file:///C:\Users\84353\chatbox\nCov_chatbox\test2.jpg")
        #return [SlotSet("numbers",response_text)]
        return
    

intent_translation_table = {
                       #"greet":"打招呼",
                       #"goodbye":"说再见",
                       #"affirm":"点头",
                       #"deny":"说不对",
                       #"thankyou":"说谢谢",
                       "search_overall":"获取疫情的总体信息",
                       "search_news":"看看有哪些新闻",
                       "search_rumors":"看看有哪些谣言被澄清了",
                       "show_trend":"看看趋势图",
                       "out_of_scope ":"闲聊会儿"
                   }   

#override default ask affirmation action
class ActionAskAffirmation(Action):
    """override default ask affirmation action
    """

    def name(self) -> Text:
        return "action_default_ask_affirmation"

    def run(
        self,
        #output_channel: "OutputChannel",
        #nlg: "NaturalLanguageGenerator",
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        intent_to_affirm = tracker.current_state()["latest_message"]["intent"]["name"]
        # an intent translation table should be offered
        if intent_translation_table.get(intent_to_affirm):
            intent_dscr = intent_translation_table[intent_to_affirm]
            affirmation_message = f"您是想{intent_dscr}吗?"
            message = {
                "text": affirmation_message,
                "buttons": [
                    {"title": "没错", "payload": f"/{intent_to_affirm}"},
                    {"title": "摇头", "payload": f"/out_of_scope"},
                ],
             }
        else:
            affirmation_message = f"抱歉，我没理解您的意图。\n但您可以让我做这些事情："
            message = {
                "text": affirmation_message,
                "buttons": [
                    {"title": "显示今日疫情简讯", "payload": f"/search_overall"},
                    {"title": "显示疫情趋势图", "payload": f"/show_trend"},
                    {"title": "显示新闻", "payload": f"/search_news"},
                    {"title": "显示最新谣言与辟谣", "payload": f"/search_rumors"},
                ],
             } 
        dispatcher.utter_message(text = message["text"],buttons = message["buttons"])
        return 
        #return [create_bot_utterance(message)]