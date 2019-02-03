import newrelic.agent

newrelic.agent.initialize('newrelic.ini')
newrelic.agent.register_application(timeout=10.0)

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import os
import json
import datetime
import myfitnesspal

import schedule
import time

import logging


@newrelic.agent.function_trace()
def login():
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)
    driver.find_element_by_id('email').send_keys(USERNAME)
    driver.find_element_by_id('password').send_keys(PASSWORD)
    driver.find_element_by_id('password').send_keys(Keys.ENTER)
    return driver


@newrelic.agent.function_trace()
def get_workout_data():
    logger.info("Logging into MapMyWalk")
    d = login()
    logger.info("Log in successful.")
    time.sleep(3)
    today = datetime.date.today()
    d.get(WORKOUTS % (today.month, today.year))
    time.sleep(3)
    pre = d.find_element_by_tag_name("pre").text
    data = json.loads(pre)
    logger.info("JSON response: %s" % data)
    wd = data['workout_data']['workouts']
    d.close()
    d.quit()
    today = str(today)
    if today not in wd:
        logger.info("No workouts found for today.")
        return None
    else:
        return wd[today]


@newrelic.agent.function_trace()
def send_workout_data():
    workout_data = get_workout_data()
    if workout_data is not None:
        for w in workout_data:
            logger.info(w)
            newrelic.agent.record_custom_event('Workout', w, application)


@newrelic.agent.function_trace()
def send_intake_data():
    client = myfitnesspal.Client(USERNAME, PASSWORD)
    day = client.get_date(datetime.datetime.now())
    totals = day.totals
    totals.update({'water': day.water})
    newrelic.agent.record_custom_event('Meal', totals, application)


@newrelic.agent.background_task()
def job():
    try:
        logger.info("Sending intake data.")
        send_intake_data()
        logger.info("Sending workout data.")
        send_workout_data()
    except Exception as e:
        logger.debug(e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    LOGIN_URL = "https://www.mapmywalk.com/auth/login/"
    WORKOUTS = "http://www.mapmywalk.com/workouts/dashboard.json?month=%s&year=%s"

    USERNAME = os.getenv('FITNESS_PAL_USERNAME')
    PASSWORD = os.getenv('FITNESS_PAL_PASSWORD')

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    application = newrelic.agent.application()

    schedule.every().day.at("23:30").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
