import json
import os
import pandas as pd
import numpy as np
import datetime as dt

MAINTAIN_ACCEPTABLE_CHANGE = 0.2

def to_signed_amt_str(amount, decimals=True):
    return ('+' if amount >= 0 else '-') + (f'{abs(amount):.2f}' if decimals else str(abs(amount)))

# TODO: decide where this data processign should live:
# in google service or other (e.g. data processing service)
# It has google-fit specific logic.
def get_daily_weight_entries(raw_data):
    df = pd.json_normalize(raw_data, 'point')

    # Transform timestamp to the date when weight was captured
    df['date'] = df['endTimeNanos'].apply(lambda x: dt.datetime.fromtimestamp(int(x) / 1e9)).dt.strftime('%Y-%m-%d')

    # We extract the weight value from the json field. In case there are multiple weights on the same date,
    # we only take the last. No reason to worry about multiple values as it's rare.
    df['last_weight'] = df['value'].apply(lambda x: round(x[-1]['fpVal'], 2))

    df.drop(columns = ['startTimeNanos', 'endTimeNanos', 'dataTypeName', 'value', 'modifiedTimeMillis', 'originDataSourceId'], inplace=True)

    # Remove outliers that were added by mistake
    df = df[(df['last_weight'] > 50) & (df['last_weight'] < 100)]

    # Store daily history for any other purpose
    df.to_csv('data/daily_history.csv')

    result = {
        'latest_date': df['date'].max(),
        'earliest_date': df['date'].min(),
        'daily_entries': df.to_dict(orient='records')
    }
    return result

def calculate_result(weight_change, goal):
    match goal:
        case 'lose':
            return 'positive' if weight_change < 0 else 'negative'
        case 'gain':
            return 'positive' if weight_change > 0 else 'negative'
        case 'maintain':
            return 'positive' if abs(weight_change) <= MAINTAIN_ACCEPTABLE_CHANGE else 'negative'

def get_weekly_aggregates(daily_entries, goal, weeks_limit=None):
    # 1. Convert daily_entries JSON to data frame
    df = pd.DataFrame.from_records(daily_entries)

    # Set date index to aggregate by week
    df['week_start'] = pd.to_datetime(df['date'])
    df.set_index('week_start', inplace=True)

    # # If date filter values are provided, filter the daily data
    # if (date_from):
    #     query_string = f"date >= '{date_from}'"
    #     df.query(query_string, inplace=True)

    # if (date_to):
    #     query_string = f"date <= '{date_to}'"
    #     df.query(query_string, inplace=True)

    # Calculate weekly averages (mean and median) using resample method
    # averages = round(df['weight'].resample('W').agg(['mean','median']).dropna(), 2)
    weekly_entries = df['last_weight'].resample('W').mean().dropna().round(2)

    # After resampling, the date of the week is end of week
    # We set the index date to beginning the week (resample results in end of week so we subtract 6 days from it)
    weekly_entries.index -= pd.DateOffset(6)

    # If weeks filter given, take N most recent weeks
    if (weeks_limit):
        weekly_entries = weekly_entries.tail(weeks_limit + 1)

    # Calculate the weight change between weeks
    weekly_entries = weekly_entries.to_frame(name='avg_weight')
    weekly_entries['weight_change'] = weekly_entries.diff().round(2).fillna(0)

     # Calculate % of weight change compared to previous week
    weekly_entries['weight_change_prc'] = (weekly_entries['weight_change'] / weekly_entries['avg_weight'] * 100).round(2).fillna(0)

     # Calculate estimated calorie deficit based on weight change
    weekly_entries['net_calories'] = (weekly_entries["weight_change"] * 500 / 0.45).round(0).fillna(0).astype(int)

    # Add positive / negative result based on goal
    weekly_entries['result'] = weekly_entries['weight_change'].apply(lambda x: calculate_result(x, goal))

    # 1st week is for comparison, it doesn't have a result
    weekly_entries.loc[weekly_entries.index[0], 'result'] = None

    # Reset index to keep date as a column
    weekly_entries.reset_index(inplace=True)

    # Change date back to date only
    weekly_entries['week_start'] = weekly_entries['week_start'].dt.strftime('%Y-%m-%d')

    # Display in the order from the most recent
    weekly_entries = weekly_entries[::-1]

    result =  {
        'entries': weekly_entries.to_dict(orient='records')
    }

    summary = {}

    summary['total_change'] = float(weekly_entries['weight_change'].iloc[:-1].sum().round(2)) if len(weekly_entries.index) > 1 else 0.00
    summary['avg_change'] = float(weekly_entries['weight_change'].iloc[:-1].mean().round(2)) if len(weekly_entries.index) > 1 else 0.00
    summary['avg_change_prc'] = float(weekly_entries['weight_change_prc'].iloc[:-1].mean().round(2)) if len(weekly_entries.index) > 1 else 0.00
    summary['avg_net_calories'] = int(weekly_entries['net_calories'].iloc[:-1].mean()) if len(weekly_entries.index) > 1 else 0
    result['summary'] = summary

    return result

# TODO - Here we will implement the logic to build text that evaluates the overall results
def get_evaluation(weekly_data):
    return None

def filter_daily_entries(daily_entries, date_from=None, date_to=None):
    if date_from:
        daily_entries = [entry for entry in daily_entries if entry['date'] >= date_from]
    if date_to:
        daily_entries = [entry for entry in daily_entries if entry['date'] <= date_to]
    return daily_entries


def load_daily_data_file(path='data/daily_data.json'):
    if os.path.exists(path):
        with open(path, 'r') as file:
            try:
                daily_entries = json.load(file)
                return daily_entries
            except json.JSONDecodeError:
                return None
    return None

def data_refresh_needed():
    daily_entries = load_daily_data_file()
    if not daily_entries:
        return True

    if len(daily_entries['daily_entries']) == 0:
        return True

    try:
        return dt.date.fromisoformat(daily_entries['latest_date']) < dt.date.today()
    except (KeyError, ValueError):
        return True