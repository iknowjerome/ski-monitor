import pandas as pd
import datetime
import requests
import os
import numpy as np

KEY = os.environ['DARKSKY_KEY']


class DarkSky:

    def __init__(self):

        self.columns = ['location', 'time', 'summary', 'icon', 'precipIntensity', 'precipProbability', 'precipType',
                        'temperature', 'apparentTemperature', 'dewPoint', 'humidity', 'pressure', 'windSpeed', 'windGust',
                        'windBearing', 'cloudCover', 'uvIndex', 'visibility', 'ozone']

    def df_template(self):
        """ Returns basic dataframe with DarkSky columns."""

        return pd.DataFrame(
            columns=self.columns)

    def post_process(self, df):
        """ Post-process df which comes from a DarkSky API call"""

        df['time'] = df['time'].apply(lambda x: datetime.datetime.fromtimestamp(x))

        df.sort_values(by='time', inplace=True)

        p_type = np.array([int(i) for i in (df['precipType']=='rain').tolist()])

        df = df[self.columns]

        df['precipSigned'] = df.loc[:, 'precipIntensity'].copy() * (1 - 2 * p_type)

        return df

    def get_past_week_darksky(self, loc_dict):
        """ Fetch hourly details for every day in the last week."""

        df = self.df_template()

        now = datetime.datetime.date(datetime.datetime.now())
        dates = [now - datetime.timedelta(days=i) for i in range(7)]

        timestamps = [datetime.datetime.combine(d, datetime.time()).timestamp() for d in dates]

        for loc in loc_dict.keys():
            lon = loc_dict[loc][0]
            lat = loc_dict[loc][1]
            for t in timestamps:
                r = requests.get(
                    'https://api.darksky.net/forecast/%s/%1.4f,%1.4f,%d' % (KEY, lon, lat, t),
                    params={'units': 'si'})

                for h in r.json()['hourly']['data']:
                    h['location'] = loc
                    df = df.append(h, ignore_index=True)

        return self.post_process(df)

    def get_nextweek_darksky(self, loc_dict, daily=False):
        """ From the DarkSky docs:

        A Forecast Request returns the current weather conditions,
        a minute-by-minute forecast for the next hour (where available),
        an hour-by-hour forecast for the next 48 hours, and a day-by-day forecast for the next week.

        """

        df = self.df_template()

        for loc in loc_dict.keys():
            lon = loc_dict[loc][0]
            lat = loc_dict[loc][1]

            r = requests.get('https://api.darksky.net/forecast/%s/%1.4f,%1.4f' % (KEY, lon, lat),
                             params={'units': 'si'})

            c = r.json()['currently']

            c['location'] = loc

            df = df.append(c, ignore_index=True)

            for h in r.json()['hourly']['data']:
                h['location'] = loc
                df = df.append(h, ignore_index=True)

            if daily:
                for d in r.json()['daily']['data']:
                    d['location'] = loc
                    df = df.append(d, ignore_index=True)

        return self.post_process(df)
