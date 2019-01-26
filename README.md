# Fitness Insights Dashboard

I have started to track my daily intake and exercise using [MyFitnessPal](https://www.myfitnesspal.com/) and other mobile apps. This project pulls data from those sources and sends to [New Relic Insights](https://newrelic.com/products/insights). This allows me to create visualisations and query my fitness and food intake data using [NRQL](https://docs.newrelic.com/docs/insights/nrql-new-relic-query-language/nrql-reference/nrql-syntax-components-functions).

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

You will also need to configure the environmental variables outlined in the installation above, for example:

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
SELECT sum(water) FROM Workout SINCE 1 week AGO TIMESERIES 1 day 
```

## Contributing

If you have ideas or suggestions on improvments that can be made to this project, please let me know!

