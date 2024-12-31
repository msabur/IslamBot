import asyncio
import configparser
from datetime import datetime
import pytz

import aiomysql

config = configparser.ConfigParser()
config.read('config.ini')

host = config['MySQL']['host']
user = config['MySQL']['user']
password = config['MySQL']['password']
database = config['MySQL']['database']

loop = asyncio.get_event_loop()


class DBHandler:
    def __init__(self, table_name: str, key_columns: list[str], value_columns: list[str], default_values: list, key: list):
        self.table_name = table_name
        self.key_columns = key_columns  # e.g in the prayer times table, user is key_column
        self.value_columns = value_columns  # and calculation_method is value_columns[0]
        self.default_values = default_values  # would be [4] in the prayer times table
        self.key = key # lookup key
        # should have len(value_columns) == len(default_values) and len(key_columns) == len(key)

    @classmethod
    async def create_connection(cls):
        connection = await aiomysql.connect(host=host, user=user, password=password, db=database,
                                            loop=loop, autocommit=True)
        return connection

    async def _get_data(self):
        try:
            connection = await self.create_connection()
        except:
            return self.default_values

        try:
            key_comparison = ' AND '.join([f"{col} = '{val}'" for col, val in zip(self.key_columns, self.key)])

            async with connection.cursor() as cursor:
                await cursor.execute(f"SELECT {', '.join(self.value_columns)} "
                                     f"FROM {self.table_name} "
                                     f"WHERE {key_comparison}")
                result = await cursor.fetchone()
                connection.close()
                if result is None:
                    return self.default_values

                return result
        except:
            connection.close()
            return self.default_values

    async def _update_data(self, *values):
        col_names = self.key_columns + self.value_columns
        value_placeholders = ', '.join(['%s' for _ in col_names]) # %s, %s, ...
        value_assignment_placeholders = ', '.join([f"{col}=%s" for col in col_names]) # col1=%s, col2=%s, ...

        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            create_sql = f"INSERT INTO {self.table_name} ({', '.join(col_names)}) " \
                         f"VALUES ({value_placeholders}) " \
                         f"ON DUPLICATE KEY UPDATE {value_assignment_placeholders}"
            await cursor.execute(create_sql, (*self.key, *values, *self.key, *values))
            connection.close()

    async def _delete_data(self):
        connection = await self.create_connection()
        key_comparison = ' AND '.join([f"{col} = '{val}'" for col, val in zip(self.key_columns, self.key)])

        async with connection.cursor() as cursor:
            delete_sql = f"DELETE FROM {self.table_name} WHERE {key_comparison}"
            await cursor.execute(delete_sql)
            connection.close()


class ServerTranslation(DBHandler):
    def __init__(self, guild_id: int):
        super().__init__(
            table_name=config['MySQL']['server_translations_table_name'],
            key_columns=['server'],
            value_columns=['translation'],
            default_values=['haleem'],
            key=[guild_id]
        )
        self.default_value = self.default_values[0]

    async def get(self) -> str:
        return (await self._get_data())[0]

    async def update(self, translation):
        return await self._update_data(translation)

    async def delete(self):
        return await self._delete_data()


class ServerTafsir(DBHandler):
    def __init__(self, guild_id: int):
        super().__init__(
            table_name=config['MySQL']['server_tafsir_table_name'],
            key_columns=['server'],
            value_columns=['tafsir'],
            default_values=['maarifulquran'],
            key=[guild_id],
        )
        self.default_value = self.default_values[0]

    async def get(self) -> str:
        return (await self._get_data())[0]

    async def update(self, tafsir):
        return await self._update_data(tafsir)

    async def delete(self):
        return await self._delete_data()


class ServerArabicTafsir(DBHandler):
    def __init__(self, guild_id: int):
        super().__init__(
            table_name=config['MySQL']['server_atafsir_table_name'],
            key_columns=['server'],
            value_columns=['atafsir'],
            default_values=['tabari'],
            key=[guild_id],
        )
        self.default_value = self.default_values[0]

    async def get(self) -> str:
        return (await self._get_data())[0]

    async def update(self, atafsir):
        return await self._update_data(atafsir)

    async def delete(self):
        return await self._delete_data()


class UserPrayerCalculationMethod(DBHandler):
    def __init__(self, user_id):
        super().__init__(
            table_name=config['MySQL']['user_prayer_times_table_name'],
            key_columns=['user_id'],
            value_columns=['calculation_method_id'],
            default_values=[4],
            key=[user_id],
        )
        self.default_value = self.default_values[0]

    async def get(self) -> int:
        result = await self._get_data()
        return int(result[0])

    async def update(self, calculation_method):
        return await self._update_data(calculation_method)

    async def delete(self):
        return await self._delete_data()


class ServerDailyPost(DBHandler):
    table_name=config['MySQL']['server_daily_post_table_name']
    key_columns=['server', 'post_type']
    value_columns=['channel', 'daily_time', 'last_send_date', 'use_arabic']
    columns = key_columns + value_columns

    # `daily_time` column is type TIME, `last_send_date` column is type DATE
    # `use_arabic` column is type BOOLEAN (1=true, 0=false)
    
    def __init__(self, guild_id: int, post_type: str):
        super().__init__(
            table_name=self.table_name, 
            key_columns=self.key_columns, 
            value_columns=self.value_columns,
            default_values=['' for _ in self.value_columns],
            key=[guild_id, post_type],
        )

    async def get(self) -> list[str]:
        return await self._get_data()

    async def update(self, channel: int, daily_time: str, last_send_date: str | None, use_arabic: bool | int):
        if last_send_date is None:
            last_send_date = "1900-01-01"
        boolToInt = lambda b: 1 if b else 0
        return await self._update_data(channel, daily_time, last_send_date, boolToInt(use_arabic))
        
    async def delete(self):
        return await self._delete_data()

    @classmethod
    async def runSql(cls, sql, params) -> list:
        connection = None
        try:
            connection = await DBHandler.create_connection()
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
                result = await cursor.fetchall()
                connection.close()

                if result is None:
                    return []

                return result
        except:
            if connection:
                connection.close()
            return []
    
    @classmethod
    async def get_pending_tasks(cls) -> list:
        now_utc = datetime.now(tz=pytz.utc)
        formatted_time = now_utc.strftime('%H:%M')
        formatted_date = now_utc.strftime('%Y-%m-%d')

        query = (
            f"SELECT {', '.join(cls.columns)} "
            f"FROM {cls.table_name} "
            f"WHERE daily_time <= %s AND last_send_date < %s"
        )
        return await cls.runSql(query, (formatted_time, formatted_date))

    @classmethod
    def parse_row(cls, row: list):
        return { column_name: str(column_value) for column_name, column_value in zip(cls.columns, row) }