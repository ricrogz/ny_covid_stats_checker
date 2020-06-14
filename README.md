# ny_covid_stats_checker
A set of simple scripts to update and check New York City statistics from
open data sources. A simple telegram bot for reporting updated statistics
is included.

Data comes from two different sources, the City and the State, so that
sometimes the reported figures do not match between the different scripts.

# Included scripts:

- **city_stats.py**: Works with data released by New York City Department of
Health. Reports the total number of cases accross the city, the total number
of cases in the selected zip codes (see the config section), total number
of hospitalized cases, and total number of deaths (confirmed and suspected).
It also calculates daily increments from one day to the next.

- **covid_bot.py**: A very simple Telegram Bot that downloads the data provided
by the New York State, and summarizes COVID cases data for the five counties in
New York City (Bronx, Kings, New York, Queens and Richmond), and messages them
over Telegram if an update is detected (it't up to you to figure out how to run
the script at the desired intervals). The reported data is:
- Number of new cases detected during the previous day, how many tests were run,
and the positive detection ratio.
- Two plots for these data over the last 30 days.
- The data series for the last 15 days.

- **covid.ipynb**: A very simple Jupyter Notebook that makes some plots based
on the same data as the covid Telegram bot. The two plot series are for the
last fortnight and since the beginning of data.

# Format of the configuration file

The config file is a simple json file, which expects the following keys:

```
{
  "NEIGHBORHOOD_ZIP_CODES": [  # A list of strings with ZIP codes in the
    "...",                     # New York Area. Data for these ZIP codes
    "...",                     # will be accumulated and reported as
    "...",                     # "close cases"
    "...",
  ],

  "SOCRATA_TOKEN": "...",  # A token for the Socrata API. The telegram bot
                           # should work without it, but data download will
                           # be rate limited.

  "TELEGRAM_CHAT_ID": int, # The integer chat id to which to report updates.
                           # You need to find this one out on your own. Check
                           # the Python Telegram docs to know how!

  "TELEGRAM_TOKEN": "..."  # The required token to allow the bot to send
                           # messages over Telegram. Check the docs on
                           # Telegram Bots on how to get one.
}
```