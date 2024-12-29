import asyncio
import configparser

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
            key_comparison = ' AND '.join([f"{col} = {val}" for col, val in zip(self.key_columns, self.key)])

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
        key_comparison_placeholder = ' AND '.join([f"{col}=%s" for col in self.key_columns])

        async with connection.cursor() as cursor:
            delete_sql = f"DELETE FROM {self.table_name} WHERE {key_comparison_placeholder}"
            await cursor.execute(delete_sql, *self.key)
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
