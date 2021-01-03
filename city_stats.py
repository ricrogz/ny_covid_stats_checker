# coding: utf-8
import io
import os
import git
import json
import datetime
import pandas as pd

pd.options.display.float_format = '{:,.2f}'.format
pd.options.display.max_rows = None
pd.options.display.width = None

CFG_FILE = 'config.json'

REPO_URL = 'https://github.com/nychealth/coronavirus-data.git'
REPO_PATH = 'coronavirus-data'
STAT_SUMMARY_FILE_NAME = 'summary.csv'
ZIP_STAT_FILE_NAME = 'data-by-modzcta.csv'

DATE_LABELS = (
    'As of:',
    'DATE_UPDATED',
)
CASES_LABELS = (
    'Cases:',
    'Case count',
    'NYC_PROBABLE_CASE_COUNT',
    'NYC_CASE_COUNT',
)
HOSPITAL_LABELS = (
    'Known hospitalizations (estimate)',
    'Hospitalizations (estimate):',
    'Total hospitalizations (estimate):',
    'Total hospitalized*:',
    'Hospitalized*:',
    'NYC_HOSPITALIZED_COUNT',
)
DEAD_LABELS = (
    'Death count',
    'Deaths:',
    'NYC confirmed deaths:',
    'NYC deaths:',
    'Confirmed',
    'Probable',
    'NYC_CONFIRMED_DEATH_COUNT',
    'NYC_PROBABLE_DEATH_COUNT',
)
DATE_FORMATS = (
    '%c',
    '"%B %d, %I:%M %p"',
    '"%B %d, %I.%M %p"',
    '"%B %d, %I %p"',
    '"%m/%d/%Y, %I:%M%p"',
)
SKIP_DATES = ('"Date, time"',)
SKIP_LABELS = (
    'MEASURE',
    'NYC_TOTAL_DEATH_COUNT',
    'NYC_TOTAL_CASE_COUNT',
)


class DailyStats:

    def __init__(self, zip_codes, data_block, zip_block=None):
        self.date = None
        self.cases = None
        self.hospital = None
        self.dead = None
        self.neighborhood = None

        for row in data_block.split('\n'):
            row = row.strip()
            try:
                label, value = row.split(',', 1)
            except ValueError as e:
                msg = str(e)
                msg += f'\nLine was: {row}'
                msg += f'\nBlock was:\n{data_block}'
                raise ValueError(msg)

            if label in SKIP_LABELS:
                continue
            elif label in DATE_LABELS:
                self.date = self._parseDate(value)
                if self.date is None:
                    return

            elif label in CASES_LABELS:
                self._updateCounter('cases', value)
                if self.cases is None:
                    return

            elif label in HOSPITAL_LABELS:
                self._updateCounter('hospital', value)

            elif label in DEAD_LABELS:
                self._updateCounter('dead', value)

            else:
                raise ValueError(f'Unknown label: {row}')

        if zip_block is not None:
            self._parse_zip_data(zip_codes, zip_block)

    def isValid(self):
        return self.date is not None and self.cases is not None

    def __str__(self):
        return f'{self.date.isoformat()} {self.cases}'

    def _updateCounter(self, attr, str):
        current = getattr(self, attr)
        if current is None:
            current = 0
        try:
            current += int(str)
        except ValueError:
            return
        setattr(self, attr, current)

    def _parseDate(self, date_time_str):
        if date_time_str in SKIP_DATES:
            return

        date_time_str = date_time_str.replace('p.m.', 'pm')
        date_time_str = date_time_str.replace('a.m.', 'am')
        date_time_str = date_time_str.replace(' at ', ' ')
        date_time_str = date_time_str.replace('Augus ', 'August ')
        date_time_str = date_time_str.replace('August10', 'August 10')

        exc = None
        for date_fmt in DATE_FORMATS:
            try:
                date = datetime.datetime.strptime(date_time_str, date_fmt)
            except ValueError as e:
                exc = e
            else:
                if date.year == 1900:
                    year = 2020
                    if date.date() < datetime.date(1900, 3, 25):
                        year += 1
                    date = date.replace(year=year)
                return date
        raise ValueError(f'Last exception: {exc}')

    def _parse_zip_data(self, zip_codes, zip_data):
        area_codes = set(zip_codes)

        for line in zip_data.split('\n'):
            items = line.strip().split(',', 4)
            if items[0] in area_codes:
                self._updateCounter('neighborhood', items[3])
                area_codes.remove(items[0])
                if not area_codes:
                    return

    def __sub__(self, other):
        ret = []
        for attr in ('date', 'cases', 'neighborhood', 'hospital', 'dead'):
            current = getattr(self, attr)
            previous = getattr(other, attr)
            if previous is None:
                previous = 0
                setattr(other, attr, 0)
            if current is None:
                ret.append(0)
                setattr(self, attr, 0)
            else:
                ret.append(current - previous)

        return ret

    def getRow(self, tabla):
        if len(tabla.index):
            last_row = tabla.iloc[-1]
        else:
            last_row = [0] * 8

        ret = [self.date.date()]
        for col, attr in enumerate((
                'cases',
                'neighborhood',
                'hospital',
                'dead',
        ), 1):

            current = getattr(self, attr)
            if current is None:
                current = 0
            ret += [current, current - last_row[2 * col - 1]]

        return pd.Series(ret, index=tabla.columns)


def clone_or_update_repo():
    try:
        git.cmd.Git(REPO_PATH).pull()
    except git.exc.GitCommandNotFound:
        git.cmd.Git(os.getcwd()).clone(REPO_URL)


def read_committed_file(file_object):
    if file_object is None:
        return None
    with io.BytesIO(file_object.data_stream.read()) as f:
        data = f.read().decode('utf-8').strip()
    if data.startswith('\ufeff'):
        data = data[1:]
    return data


def get_commited_file(commit, fname):
    for f in (f'totals/{fname}', fname):
        try:
            return commit.tree / f
        except KeyError:
            pass
    return None


def iter_data(cfg, repo):
    repo = git.Repo(repo)
    for commit in repo.iter_commits('master', reverse=True):
        summary_file = get_commited_file(commit, STAT_SUMMARY_FILE_NAME)
        summary_data = read_committed_file(summary_file)

        if summary_data is None or '<<<<<<< HEAD' in summary_data:
            continue

        zip_file = get_commited_file(commit, ZIP_STAT_FILE_NAME)
        zip_data = read_committed_file(zip_file)

        try:
            yield DailyStats(cfg['NEIGHBORHOOD_ZIP_CODES'], summary_data,
                             zip_data)
        except ValueError as e:
            print(f"Error at commit {commit.hexsha}:\n\t{str(e)}")
            raise


def parse_repo(cfg):
    clone_or_update_repo()

    tabla = pd.DataFrame([],
                         columns=[
                             'Date',
                             'Cases',
                             'Delta_Cases',
                             'Close_Cases',
                             'Delta_Close_Cases',
                             'Hospitalized',
                             'Delta_Hospitalized',
                             'Dead',
                             'Delta_Dead',
                         ])

    for stat in iter_data(cfg, REPO_PATH):
        if not stat.isValid():
            continue

        num_rows = len(tabla.index)
        if num_rows != 0:
            last_row = tabla.tail(1)
            if stat.date.date() == last_row.iloc[0]['Date']:
                tabla.drop(last_row.index, inplace=True)
            elif stat.date.date() < last_row.iloc[0]['Date']:
                continue

        data = stat.getRow(tabla)
        tabla = tabla.append(data, ignore_index=True)

    tabla.set_index('Date', inplace=True)
    tabla.index = pd.DatetimeIndex(tabla.index)
    tabla.index -= datetime.timedelta(days=1)

    return tabla


def main():
    with open(CFG_FILE) as f:
        cfg = json.load(f)
    tabla = parse_repo(cfg)
    print(tabla)


if __name__ == '__main__':
    main()
