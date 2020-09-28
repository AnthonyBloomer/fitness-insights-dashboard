# Fitness Insights Dashboard

## Introduction

As a motivator to maintain a healthy diet and to get into a routine of daily workouts, I have started to track my intake and exercise habits using MyFitnessPal and other mobile applications. Pulling data from those sources and creating custom events in New Relic Insights allows me to keep track of my progress and provides a way for me to query my data using NRQL and to create visualisations.

## Data Sources 

The two main applications I use for tracking is [MyFitnessPal](https://www.myfitnesspal.com/) and [MapMyWalk](https://www.mapmywalk.com/my_home/). MyFitnessPal allows you to track your diet and exercise to determine optimal caloric intake and nutrients for your overall goal. MapMyWalk allows you to track cardiovascular activities such as running, walking and even stationary bike exercises.

Although MyFitnessPal does have an API, it is private-access only. To get around this, I found a Python library called [python-myfitnesspal](https://github.com/coddingtonbear/python-myfitnesspal) which allows you to scrape your data from MyFitnessPal. See the example below:

``` python
import myfitnesspal

client = myfitnesspal.Client('my_username')
day = client.get_date(2013, 3, 2)
day
# >> <03/02/13 {'sodium': 3326, 'carbohydrates': 369, 'calories': 2001, 'fat': 22, 'sugar': 103, 'protein': 110}>
```

For a daily summary of your nutrition information, you can use a Day object's totals property:

```
day.totals
# >> {'calories': 2001,
#     'carbohydrates': 369,
#     'fat': 22,
#     'protein': 110,
#     'sodium': 3326,
#     'sugar': 103}
```

If you want to see the amount of water you've recorded:

```
day.water
# >> 1
```

Perfect. These are exactly the data points I am interested in. So, once a day, I call the API to get those values and record a custom event using the Event API:

``` python
def send_intake_data():
    client = myfitnesspal.Client(USERNAME, PASSWORD)
    day = client.get_date(datetime.datetime.now())
    totals = day.totals
    totals.update({'water': day.water})
    record_custom_event('Meal', totals)
```

Similarly to MyFitnessPal, MapMyWalk does have an API but it is private access only. To address this issue, I wrote a simple script using Selenium which logs into the MapMyWalk website and then goes to a JSON resource which holds my workout data. Once every day, I call this script to get workout data for that day and then record a custom event in Insights:

``` python
def login():
    logger.info("Logging into MapMyWalk")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)
    driver.find_element_by_id('email').send_keys(USERNAME)
    driver.find_element_by_id('password').send_keys(PASSWORD)
    driver.find_element_by_id('password').send_keys(Keys.ENTER)
    return driver

def get_workout_data():
    d = login()
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

def send_workout_data():
    workout_data = get_workout_data()
    if workout_data is not None:
        for w in workout_data:
            logger.info(w)
            record_custom_event('Workout', w)
```

See the dashboard below:

![Image](https://i.imgur.com/D9fVKBE.png)

## Installation

This project uses [python-myfitnesspal](https://github.com/coddingtonbear/python-myfitnesspal) to programatically interact with and analyze the information I have entered into MyFitnessPal. To authenticate, you'll need to export your username and password as environment variables:

``` shell
export FITNESS_PAL_USERNAME='YOUR_USERNAME'
export FITNESS_PAL_PASSWORD='YOUR_PASSWORD'
```

I'm using Selenium and the ChromeDriver to automate data retrieval from the MapMyWalk website. You will need to have Google Chrome and [ChromeDriver](http://chromedriver.chromium.org) installed. If you are using macOS, you can install ChromeDriver using Homebrew:

``` shell
brew cask install chromedriver
```

To send metrics to New Relic Insights, you will also need to export your application name and license key:

``` shell
export NEW_RELIC_LICENSE_KEY='YOUR_LICENSE_KEY'
export NEW_RELIC_APP_NAME='YOUR_APP_NAME'
```

Then, create a new Virtual Environment and install the project requirements:

``` shell
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Finally, launch the worker:

``` shell
python fitnesspal.py
```

The program uses [schedule](https://pypi.org/project/schedule/) to send metrics once a day at 23:30pm.

### Deploying to Heroku

Since I'm using Selenium to automate data retrieval from MapMyWalk, you'll need to install the following buildpacks:

- [heroku-buildpack-xvfb-google-chrome](https://github.com/heroku/heroku-buildpack-xvfb-google-chrome)
- [heroku-buildpack-chromedriver](https://github.com/heroku/heroku-buildpack-chromedriver)

You will also need to configure the environment variables outlined in the installation above, for example:

```
heroku config:set NEW_RELIC_LICENSE_KEY=YOUR_LICENSE_KEY
```

## Querying Insights Data

This tool creates two custom events, `Meal` and `Workout`, which you can query using NRQL in Insights. 

### Examples 

Get your average calorie intake since 1 week ago:

``` sql
SELECT average(calories) FROM Meal SINCE 1 week AGO TIMESERIES 1 day 
```

Get the total number of steps walked since 1 week ago:

``` sql
SELECT sum(steps) FROM Workout SINCE 1 week AGO TIMESERIES 1 day 
```

Get the total amount of water consumed:

``` sql
SELECT sum(water) FROM Meal SINCE 1 week AGO TIMESERIES 1 day 
```

## Contributing

If you have ideas or suggestions on improvments that can be made to this project, please let me know!

