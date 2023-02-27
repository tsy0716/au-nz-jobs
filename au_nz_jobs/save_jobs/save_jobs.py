import os
import pandas as pd
from sql import Sql

def save_jobs(df_dict, format='csv',single_table = True, path='data'):
    # check if the path exists, if not, create the path
    if not os.path.exists(f'{path}'):
        # create the path
        os.makedirs(f'{path}')

    if single_table:
        table_names = ['jobs_wide']
    else:
        # exclude jobs_wide table in the dictionary
        table_names = [table for table in df_dict.keys() if table != 'jobs_wide']

    # initialize the Excel file and the writer
    if format == 'excel':
        # create the Excel file
        excel = pd.ExcelWriter(f'{path}/jobs.xlsx', engine='xlsxwriter')

    # loop through the table names to find the corresponding DataFrame
    for table in table_names:
        # get the DataFrame
        df = df_dict[table]
        # save the DataFrame to local file
        if format == 'csv':
            # save the DataFrame to csv file
            df.to_csv(f'{path}/{table}.csv', index=False)
        elif format == 'excel':
            # convert all datetime columns to date, check for dtype containing 'datetime'
            for col in df.columns[df.dtypes.astype(str).str.contains('datetime')]:
                # convert the datetime column to date
                df[col] = df[col].dt.date
            # initiate the Excel writer
            with pd.ExcelWriter(f'{path}/jobs.xlsx', engine='openpyxl', mode='a') as writer:
                # save the DataFrame to Excel file
                df.to_excel(writer, sheet_name=table, index=False)
        else:
            # raise an error if the format is not supported
            raise ValueError(f'format {format} is not supported')

    # close the Excel file
    if format == 'excel':
        # close the Excel file
        excel.close()

# define a function to write the job table to sqlite
def save_jobs_sqlite(df_dict, path='data'):
    # check for the existence of the database, path including the database name
    if not os.path.exists(f'{path}'):
        # create the database
        open(f'{path}', 'a').close()
    # initialize the sql connection
    sql = Sql(path=f'{path}')
    # loop through the table names to find the corresponding DataFrame
    for table in df_dict.keys():
        # get the DataFrame
        df = df_dict[table]
        # generate the key for the table, e.g. 'classification': 'classification_id'
        key = f'{table[:-1]}_id'
        # if jobs table, use 'job_id' as the key
        if table == 'jobs':
            key = 'job_id'
        # check if the table exists, if not, create the table
        if table not in sql.get_all_tables_names():
            sql.create_table(df, table, key=key)
        # if the table exists, update the table
        else:
            sql.update_table(df, table, key=key, method='insert')
