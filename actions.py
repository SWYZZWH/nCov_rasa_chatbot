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

#response_templates = {
#    "current":"Temperature:{}\nCondition:{}",
#    "someday":"Max Temperature:{}\nMin Temperature:{}\nCondition:{}\n"
#}

def create_url(api_pattern,paras):
    url = base_url
    if api_pattern in api_patterns.keys():
        url += api_pattern
        
    if paras:
        url += "?"
        
    url += "&".join([key+"="+value for key,value in paras.items()])
    return url



