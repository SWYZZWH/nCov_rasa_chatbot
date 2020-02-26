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
    "news":"最新新闻:\n",
    "rumors":"最新谣言与辟谣:\n"
}

def create_url(api_pattern,paras):
    url = base_url
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
        
        
        #location = tracker.get_slot("location")
        location = None
        paras = {}
        if location:
            api_pattern = "area"
            #paras["province"] = province
        else:
            api_pattern = "overall"
        latest = 1
        #paras["latest"] = latest
        
        
        #grab all information first,then filter
        full_url = create_url(api_pattern,paras)
        ret = requests.get(full_url).json()
        print(full_url)
        print(ret)
        
        response_paras = []
        if not ret.get("results"):
            dispatcher.utter_message(text="错误！")
            return [SlotSet("numbers","null")]
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
                    return [SlotSet("overall_info","null")] 
                            
                response_paras.append(location)
            else:
                loc_match = results[0]
            print(loc_match)
                
            #print results
            response_paras += [loc_match["currentConfirmedCount"],loc_match["confirmedCount"],loc_match["suspectedCount"],\
                                  loc_match["curedCount"],loc_match["deadCount"]]
            
            response_text = response_templates[api_pattern].format(*response_paras)
                  
        dispatcher.utter_message(text=response_text)
        #eturn [SlotSet("numbers",response_text)]
        return
    
class ActionSearchNews(Action):
    def name(self) -> Text:
        return "action_search_news"
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        paras = {}
        paras["num"] = "3" #api default is 10;should be able to change according to users' need
        api_pattern = "news"
        
        #grab all information first,then filter
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
            for news in results:                        
                response_text += news["title"] + "\n" 
                # add more infomation of news
                
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
        paras["num"] = "3" #api default is 10;should be able to change according to users' need
        api_pattern = "rumors"
        
        #grab all information first,then filter
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