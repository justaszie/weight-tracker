import json
import os
import pandas as pd
import datetime as dt
from googleapiclient.discovery import build # Build fitness service used to make requests
from googleapiclient.errors import HttpError

MAINTAIN_ACCEPTABLE_CHANGE = 0.2

def to_signed_amt_str(amount, decimals=True):
    return ('+' if amount >= 0 else '-') + (f'{abs(amount):.2f}' if decimals else str(abs(amount)))

def get_gfit_data(creds):
    dataset = None
    fitness_service = build('fitness', 'v1', credentials=creds)

    # Get all available data
    date_from_ns_timestamp = 0
    tomorrow = dt.datetime.now() + dt.timedelta(days=1)
    date_to_ns_timestamp = int(tomorrow.timestamp() * 1e9)

    DATA_SOURCE = "derived:com.google.weight:com.google.android.gms:merge_weight"
    DATA_SET = f"{date_from_ns_timestamp}-{date_to_ns_timestamp}"

    # print(f" Data Set ID: {DATA_SET}")
    # # Using google api library to build the HTTP request object to call Fit API with relevant parameters
    request = fitness_service.users().dataSources().datasets().get(userId='me', dataSourceId=DATA_SOURCE, datasetId=DATA_SET)

    try:
        dataset = request.execute()
        fitness_service.close()
    except HttpError as e:
        print('Error response status code : {}, reason : {}'.format(e.resp.status, e.error_details))
        fitness_service.close()
    finally:
        return dataset

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
    df = pd.DataFrame.from_dict(daily_entries['daily_entries'])

    # Set date index to aggregate by week
    df['week_start'] = pd.to_datetime(df['date'])
    df.set_index('week_start', inplace=True)

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

    # Replace NaN values with 0 for the first dummy week
    # weekly_entries.fillna(value=0, inplace=True)

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

    print(weekly_entries)

    result =  {
        'entries': weekly_entries.to_dict(orient='records')
    }

    summary = {}
    summary['total_change'] = float(weekly_entries['weight_change'].iloc[:-1].sum().round(2))
    summary['avg_change'] = float(weekly_entries['weight_change'].iloc[:-1].mean().round(2))
    summary['avg_change_prc'] = float(weekly_entries['weight_change_prc'].iloc[:-1].mean().round(2))
    summary['avg_net_calories'] = int(weekly_entries['net_calories'].iloc[:-1].mean())
    result['summary'] = summary

    return result

# TODO - Here we will implement the logic to build text that evaluates the overall results
def get_evaluation(weekly_data):
    return None

def load_daily_data_file(path='data/daily_entries.json'):
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