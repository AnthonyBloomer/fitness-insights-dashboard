import newrelic.agent

newrelic.agent.initialize('newrelic.ini')
newrelic.agent.register_application(timeout=10.0)

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import os
import json
import datetime
import myfitnesspal

import schedule
import time

LOGIN_URL = "https://www.mapmywalk.com/auth/login/"
WORKOUTS = "http://www.mapmywalk.com/workouts/dashboard.json?month=%s&year=%s"

USERNAME = os.getenv('FITNESS_PAL_USERNAME')
PASSWORD = os.getenv('FITNESS_PAL_PASSWORD')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)


@newrelic.agent.function_trace()
def login():
    driver.get(LOGIN_URL)
    driver.find_element_by_id('email').send_keys(USERNAME)
    driver.find_element_by_id('password').send_keys(PASSWORD)
    driver.find_element_by_id('password').send_keys(Keys.ENTER)
    return driver


@newrelic.agent.function_trace()
def get_workout_data():
    d = login()
    today = datetime.date.today()
    d.get(WORKOUTS % (today.month, today.year))
    pre = d.find_element_by_tag_name("pre").text
    data = json.loads(pre)
    wd = data['workout_data']['workouts']
    if today not in wd:
        return None
    else:
        return wd[today]


@newrelic.agent.function_trace()
def send_workout_data():
    application = newrelic.agent.application()
    workout_data = get_workout_data()
    if workout_data is not None:
        for w in workout_data:
            newrelic.agent.record_custom_event('WorkoutData', w, application)


@newrelic.agent.function_trace()
def send_intake_data():
    client = myfitnesspal.Client(USERNAME, PASSWORD)
    day = client.get_date(datetime.datetime.now())
    application = newrelic.agent.application()
    totals = day.totals
    totals.update({
        'water': day.water
    })
    newrelic.agent.record_custom_event('MealData', totals, application)


@newrelic.agent.background_task()
def job():
    send_intake_data()
    send_workout_data()


if __name__ == '__main__':
    '''
    schedule.every().day.at("23:30").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
    '''
    send_workout_data()
    send_intake_data()
