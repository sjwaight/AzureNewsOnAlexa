import logging
import os
import requests
import json

from datetime import datetime, timedelta, timezone, tzinfo

import azure.functions as func
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler

from bs4 import BeautifulSoup # xml parsing

class ReadItemsFromDate(AbstractRequestHandler):
    """Handler for AZURENEWS.TopFive Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ReadItemsFromADate")(handler_input)

    def handle(self, handler_input):

        # ending = datetime.now("%Y-%m-%d")
        # starting = ending + timedelta(days=1)
        speak_output = "There are no new Azure items currently available for today."

        # updatelist = get_updates_rss(startDate=starting,endDate=ending)

        # if len(updatelist) > 0:

        #     # type: (HandlerInput) -> Response
        #     speak_output = "Here are the top 5 Azure news items."

        #     for item in updatelist[:5]:
        #         speak_output += item["title"]

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ReadTopFiveItems(AbstractRequestHandler):
    """Handler for ReadTopFive Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ReadTopFive")(handler_input)

    def handle(self, handler_input):

        ending =  datetime.now() 
        starting = ending + timedelta(days=-7)

        speak_output = "There are no new Azure items currently available for today."

        updatelist = get_updates_rss(startDate=starting,endDate=ending)

        if len(updatelist) > 0:

            # type: (HandlerInput) -> Response
            speak_output = "Here are the most recent 5 Azure news items."

            item_count = 1

            for item in updatelist[:5]:
                speak_output += " Item " + str(item_count) + ': <break time="0.5s"/>' + item["title"] + '<break time="1s"/>'
                item_count+=1

            speak_output += " That's the most recent 5 announcements on Azure!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hi There! I'm the Azure News Service and I can read you the latest Azure cloud news. Ask for the top five most recent items or ask to hear items from a specific date."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):

    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True


    def handle(self, handler_input, exception):

        # type: (HandlerInput, Exception) -> Response
        logging.error(exception, exc_info=True)
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return(
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# RSS scraping function
# Based mostly on: https://github.com/mattdood/web_scraping_example/blob/master/scraping.py
def get_updates_rss(startDate, endDate):
    article_list = []

    try:
        # execute my request, parse the data using XML
        # parse using BS4
        r = requests.get(os.environ["UpdatesURL"])
        soup = BeautifulSoup(r.content, features='xml')

        # select only the "items" I want from the data
        updates = soup.findAll('item')

        # for each "item" I want, parse it into a list
        for a in updates:

            # Get publication date
            published = a.find('pubDate').text
            pubDate = datetime.strptime(a.find('pubDate').text, "%a, %d %b %Y %H:%M:%S Z")

            # only include items falling within our requested date range
            if (pubDate >= startDate and pubDate <= endDate):

                title = a.find('title').text
                link = a.find('link').text
            
                # basic parse to flag announcement types
                if "preview" in title.lower():
                     announcement_type = "preview"
                else:
                    announcement_type = "GA"

                # create an "article" object with the data
                # from each "item"
                article = {
                    'title': title,
                    'link': link,
                    'published': published,
                    'antype': announcement_type
                    }

                # append my "article_list" with each "article" object
                article_list.append(article)
        
        # after the loop, dump my saved objects into a .txt file
        return article_list
    except Exception as e:
        logging.exception("Couldn't scrape the Azure Updates RSS feed")



def main(req: func.HttpRequest) -> func.HttpResponse:
    # logging.info('Python HTTP trigger function processed a request.')

    skill_builder = SkillBuilder()

    skill_builder.add_request_handler(LaunchRequestHandler())
    skill_builder.add_request_handler(ReadTopFiveItems())
    skill_builder.add_request_handler(ReadItemsFromDate())
    skill_builder.add_exception_handler(CatchAllExceptionHandler())

    webservice_handler = WebserviceSkillHandler(skill=skill_builder.create())

    response = webservice_handler.verify_request_and_dispatch(req.headers, req.get_body().decode("utf-8"))

    return func.HttpResponse(json.dumps(response),mimetype="application/json")