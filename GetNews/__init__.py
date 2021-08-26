import logging
import os
import requests
import json
import azure.functions as func
import ask_sdk_core.utils as ask_utils

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler


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

                article = {
                    'title': title,
                    'link': link,
                    'published': published,
                    'antype': announcement_type
                    }

                article_list.append(article)
        
        return article_list
    except Exception as e:
        logging.exception("Couldn't scrape the Azure Updates RSS feed")

# Parse the list and build an SSML string to be main body of response
def generate_list_respose(updatelist):

    speak_output = ""
    item_count = 1

    for item in updatelist[:5]:
        speak_output += " Item " + str(item_count) + ': <break time="0.5s"/>' + item["title"] + '.<break time="1s"/>\r\n'
        item_count+=1

    return speak_output

class ReadItemsFromDate(AbstractRequestHandler):
    """Handler for ReadItemsFromDate Intent."""
    def can_handle(self, handler_input):

        return ask_utils.is_intent_name("ReadItemsFromDate")(handler_input)

    def handle(self, handler_input):

        # Extract the date value from the slot for this intent
        # In this case we are going to assume it's a valid date and not check
        news_date_raw = ask_utils.get_slot_value(handler_input,"newsDate")

        logging.info(f"Called Skill Handler for ReadItemsFromDate Intent with 'newsDate' Slot value of '{news_date_raw}'.")

        # Default to there being no news available for this date. Date format is fine - Alexa will handle parsing on return.
        speak_output = f"I couldn't find any Azure news for {news_date_raw}."

        # Calculate the date window for updates
        ending = datetime.strptime(news_date_raw,"%Y-%m-%d")
        starting = ending + timedelta(days=-1)

        updatelist = get_updates_rss(startDate=starting,endDate=ending)

        if len(updatelist) > 0:

            speak_output = f"Here are the top Azure news items from {news_date_raw}."

            speak_output+= generate_list_respose(updatelist)

            speak_output += f" That's the top Azure news from {news_date_raw}!"

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

        logging.info("Called Skill Handler for ReadTopFive Intent.")

        speak_output = "There are no new Azure items currently available for today."

        ending =  datetime.now() 
        starting = ending + timedelta(days=-7)

        updatelist = get_updates_rss(startDate=starting,endDate=ending)

        if len(updatelist) > 0:
            speak_output = "Here are the most recent 5 Azure news items."

            speak_output+= generate_list_respose(updatelist)

            speak_output += " That's the most recent 5 announcements on Azure!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for LaunchRequest."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):

        logging.info("Called Skill Handler for LaunchRequest Intent.")

        speak_output = "Hi there! I'm the Azure news service and I can read you the latest Azure cloud news.\r\nYou can ask for the latest news by saying <break time='0.5s'/>'latest news', or ask for the top news items from a specific date by saying <break time='0.5s'/>'top news from'<break time='0.5s'/> and then the date, making sure to include the year."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End Request."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):

        logging.info("Called Skill Handler for SessionEndedRequest Intent.")

        speak_output = "Thanks for using the Azure news service! Good-bye for now."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):

        logging.info("Called Skill Handler for AMAZON.HelpIntent Intent.")

        speak_output = "You are using the Azure cloud news service. You can ask for the latest news by saying <break time='0.5s'/>'latest news', or ask for the top news items from a specific date by saying <break time='0.5s'/>'top news from'<break time='0.5s'/> and then the date, making sure to include the year."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye from the Azure cloud news service!"

        logging.info("Called Skill Handler for Cancel or Stop Intents.")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logging.error(exception, exc_info=True)
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return(
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# Main Azure Function entry point
def main(req: func.HttpRequest) -> func.HttpResponse:

    skill_builder = SkillBuilder()
    skill_builder.skill_id = os.environ["AlexaSkillID"]
    skill_builder.add_request_handler(LaunchRequestHandler())
    skill_builder.add_request_handler(ReadTopFiveItems())
    skill_builder.add_request_handler(ReadItemsFromDate())
    skill_builder.add_request_handler(HelpIntentHandler())
    skill_builder.add_request_handler(CancelOrStopIntentHandler())
    skill_builder.add_request_handler(SessionEndedRequestHandler())
    skill_builder.add_exception_handler(CatchAllExceptionHandler())

    webservice_handler = WebserviceSkillHandler(skill=skill_builder.create())

    response = webservice_handler.verify_request_and_dispatch(req.headers, req.get_body().decode("utf-8"))

    return func.HttpResponse(json.dumps(response),mimetype="application/json")