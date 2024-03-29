#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import json
import telegram
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from nys_soda import get_data

CFG_FILE = 'config.json'
STATE_FILE = 'last_covid_data.json'


class TelegramGateway:

    def __init__(self, token, chat_id):
        self.bot = telegram.Bot(token)
        self.chat_id = chat_id

    def send_msg(self, msg, chat=None):
        # TelegramGateway().send('This is a test message')

        self.bot.send_message(chat_id=chat if chat else self.chat_id, text=msg)

    def send_img_bytes(self, img, chat=None):
        self.bot.send_photo(chat_id=chat if chat else self.chat_id, photo=img)


def get_last_timestamp():
    if not os.path.isfile(STATE_FILE):
        return datetime.min
    with open(STATE_FILE) as f:
        timestamp = json.load(f)
    return datetime.fromisoformat(timestamp)


def set_last_timestamp(timestamp):
    with open(STATE_FILE, 'w') as f:
        json.dump(timestamp.isoformat(), f)


def create_plots(data, buffer):
    plot_columns = (['new_cases', 'new_cases_ave'], ['ratio', 'ratio_ave'])
    plot_legends = (['New Cases', '7 day average'],
                    ['Positive Test Ratio', '7 day average'])
    rolling_period = 7

    for (src, dst) in plot_columns:
        data[dst] = data[src].rolling(rolling_period).mean()

    fig, axes = plt.subplots(ncols=2, figsize=(15, 8))

    for axis, column, legend in zip(axes, plot_columns, plot_legends):
        data[-30:][column].plot(ax=axis, rot=-60)
        axis.xaxis.set_major_locator(
            mdates.WeekdayLocator(byweekday=mdates.MO))
        axis.xaxis.set_minor_locator(mdates.DayLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axis.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axis.grid(which='major', linestyle=':', linewidth='2')
        axis.grid(which='minor', linestyle=':', linewidth='0.5')
        axis.legend(legend)

    plt.savefig(buffer, format='png', dpi=300)
    buffer.seek(0)


def main():
    with open(CFG_FILE) as f:
        cfg = json.load(f)

    last = get_last_timestamp()
    data = get_data(cfg['SOCRATA_TOKEN'])
    timestamp = data.index[-1]
    if timestamp > last:
        set_last_timestamp(timestamp)

        t = TelegramGateway(cfg['TELEGRAM_TOKEN'], cfg['TELEGRAM_CHAT_ID'])
        t.send_msg(f'COVID data was updated:\ndate{str(data[-1:])[4:]}')

        # Do not report averages in table -- too wide
        # for phone screens
        summary_15_days = f'date{str(data[-15:])[4:]}'

        with io.BytesIO() as buffer:
            create_plots(data, buffer)

            t.send_img_bytes(buffer)

        t.send_msg(summary_15_days)


if __name__ == "__main__":
    main()
