import datetime
import json
import logging
import os
import time

import myfitnesspal
import requests
import schedule
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def record_custom_event(name, event):
    event.update({"eventType": name})
    headers = {
        "X-Insert-Key": os.getenv("NEW_RELIC_INSERT_KEY"),
    }
    req = requests.post(
        "https://insights-collector.newrelic.com/v1/accounts/%s/events"
        % os.getenv("NEW_RELIC_ACCOUNT_ID"),
        headers=headers,
        json=event,
    )
    print(req.content)


def login():
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)
    driver.find_element_by_id("email").send_keys(USERNAME)
    driver.find_element_by_id("password").send_keys(PASSWORD)
    driver.find_element_by_id("password").send_keys(Keys.ENTER)
    return driver


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
    wd = data["workout_data"]["workouts"]
    d.close()
    d.quit()
    today = str(today)
    if today not in wd:
        logger.info("No workouts found for today.")
        return None
    else:
        return wd[today]


def send_workout_data():
    workout_data = get_workout_data()
    if workout_data is not None:
        for w in workout_data:
            logger.info(w)
            record_custom_event("Workout", w)


def send_intake_data():
    client = myfitnesspal.Client(USERNAME, PASSWORD)
    day = client.get_date(datetime.datetime.now())
    totals = day.totals
    totals.update({"water": day.water})
    record_custom_event("Meal", totals)


def job():
    try:
        logger.info("Sending intake data.")
        send_intake_data()
        logger.info("Sending workout data.")
        send_workout_data()
    except Exception as e:
        logger.debug(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    LOGIN_URL = "https://www.mapmywalk.com/auth/login/"
    WORKOUTS = "http://www.mapmywalk.com/workouts/dashboard.json?month=%s&year=%s"

    USERNAME = os.getenv("FITNESS_PAL_USERNAME")
    PASSWORD = os.getenv("FITNESS_PAL_PASSWORD")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    schedule.every().day.at("23:30").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
