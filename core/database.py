import aiosqlite

async def query_table(query: str, params: set) -> list:
    rows = []

    async with aiosqlite.connect('./db/test.db') as db:
        async with db.execute(query, params) as cursor:
            async for row in cursor:
                rows.append(list(row))

    return rows

async def insert_user_account(account_name: str, real_name: str, password: str) -> None:
    query = """INSERT INTO users(
                account_name,
                real_name,
                password
            ) VALUES (?,?,?);"""

    async with aiosqlite.connect('./db/test.db') as db:
        await db.execute(query, (account_name, real_name, password,))
        await db.commit()