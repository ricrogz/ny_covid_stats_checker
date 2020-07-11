# coding: utf-8
import numpy as np
import pandas as pd
from sodapy import Socrata

pd.options.display.float_format = '{:,.3f}'.format
pd.options.display.max_rows = None
pd.options.display.width = None

DATA_URL = "health.data.ny.gov"


def pull_covid_data(token=None):
    client = Socrata(DATA_URL, token)
    return client.get(
        "xdss-u53e",
        select=
        "test_date as date, SUM(new_positives) AS new_cases, SUM(total_number_of_tests) AS tests",
        where="county IN ('Bronx', 'Queens', 'Kings', 'New York', 'Richmond')",
        group="test_date",
        order="test_date ASC",
        limit=1000)


def import_data(raw_data):
    data = pd.DataFrame.from_records(raw_data, index='date')
    data.index.name = None
    data.index = pd.to_datetime(data.index)
    data['new_cases'] = pd.to_numeric(data['new_cases'])
    data['tests'] = pd.to_numeric(data['tests'])
    data['ratio'] = (100. * data['new_cases'] / data['tests']).replace(
        np.nan, 0.)
    return data


def get_data(token=None):
    raw_data = pull_covid_data(token)
    return import_data(raw_data)
