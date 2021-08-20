import logging
import os
import requests # pulling data

from datetime import datetime, timedelta, timezone

import azure.functions as func
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler

from bs4 import BeautifulSoup # xml parsing

# def handle_alexa_request():

class ReadTopFiveItems(AbstractRequestHandler):
    """Handler for AZURENEWS.TopFive Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ReadTopFive")(handler_input)

    def handle(self, handler_input):

        #updatelist = get_updates_rss(startDate=starting,endDate=ending)

        # type: (HandlerInput) -> Response
        speak_output = "Reading the top 5 news items."

        return (
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

    response = "{}"

    try:

        skill_builder = SkillBuilder()
        skill_builder.request_handler(ReadTopFiveItems())

        webservice_handler = WebserviceSkillHandler(skill=skill_builder.create())

        response = webservice_handler.verify_request_and_dispatch(req.headers, req.get_body().decode("utf-8"))

    except Exception:
        logging.exception("Error!")

    return func.HttpResponse(response)
