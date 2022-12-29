import os
import sqlite3

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from api_yamdb.settings import STATICFILES_DIRS

DATA_PATH = os.path.join(STATICFILES_DIRS[0], 'data/')


class Command(BaseCommand):
    help = 'Imports data from csv file to database specified table'

    def add_arguments(self, parser):
        parser.add_argument('csv_name', type=str)
        parser.add_argument('table_name', type=str)

    def handle(self, *args, **options):
        conn = sqlite3.connect('db.sqlite3')
        file_path = (DATA_PATH
                     + options['csv_name']
                     + '.csv')
        table_name = options['table_name']
        try:
            df = pd.read_csv(file_path)
            print(df)
            df.to_sql(
                table_name,
                conn,
                if_exists='append',
                index=False
            )
        except Exception as e:
            raise CommandError(f'Error: {e}')
