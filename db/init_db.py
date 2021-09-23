"""This script initializes the sqllite for use with VoWmud for the first time"""
import aiosqlite
import asyncio
import bcrypt

async def table_create_users(db: aiosqlite.Connection) -> None:
    """This function creates the users table in database"""
    query = """CREATE TABLE IF NOT EXISTS users (
        id integer PRIMARY KEY,
        account_name text NOT NULL,
        real_name text NOT NULL,
        password text NOT NULL
    );
    """

    await db.execute(query)
    await db.commit()

async def table_create_rooms_general(db: aiosqlite.Connection) -> None:
    """This function creates the rooms_general table in database"""
    query = """CREATE TABLE IF NOT EXISTS rooms_general (
        id integer NOT NULL PRIMARY KEY,
        area_name text NOT NULL,
        room_number integer NOT NULL,
        room_name text NOT NULL,
        room_description text NOT NULL
    );
    """

    await db.execute(query)
    await db.commit()

async def table_create_rooms_connections(db: aiosqlite.Connection) -> None:
    """This function creates the rooms_general table in database"""
    query = """CREATE TABLE IF NOT EXISTS rooms_connections (
        id integer NOT NULL PRIMARY KEY,
        area_name text NOT NULL,
        room_number integer NOT NULL,
        exit_text text NOT NULL,
        exit_type text NOT NULL,
        connecting_area text NOT NULL,
        connecting_room integer NOT NULL,
        active integer NOT NULL
    );
    """

    await db.execute(query)
    await db.commit()

async def table_create_rooms_switches(db: aiosqlite.Connection) -> None:
    """This function creates the rooms_switches table in database"""
    query = """CREATE TABLE IF NOT EXISTS rooms_connections (
        id integer NOT NULL PRIMARY KEY,
        area_name text NOT NULL,
        room_number integer NOT NULL,
        switch_text text NOT NULL,
        switch_active integer NOT NULL
    );
    """

    await db.execute(query)
    await db.commit()

async def insert_test_users(db: aiosqlite.Connection) -> None:
    """This function inserts test users in a fresh db"""
    query = """INSERT INTO users(
                account_name,
                real_name,
                password
            ) VALUES (?,?,?);"""

    await db.execute(query, ('testuser1', bcrypt.hashpw('John Doe'.encode(), bcrypt.gensalt()), bcrypt.hashpw('blahblahblah'.encode(), bcrypt.gensalt()),))
    await db.execute(query, ('testuser2', bcrypt.hashpw('John Doe'.encode(), bcrypt.gensalt()), bcrypt.hashpw('blahblahblah'.encode(), bcrypt.gensalt()),))
    await db.execute(query, ('testuser3', bcrypt.hashpw('John Doe'.encode(), bcrypt.gensalt()), bcrypt.hashpw('blahblahblah'.encode(), bcrypt.gensalt()),))
    await db.commit()

async def insert_test_rooms(db: aiosqlite.Connection) -> None:
    """This function inserts test rooms in a fresh db"""
    query_insert_rooms_general = """INSERT INTO rooms_general(
            area_name,
            room_number,
            room_name,
            room_description
        ) VALUES (?,?,?,?);
        """

    query_insert_rooms_connections = """INSERT INTO rooms_connections(
            area_name,
            room_number,
            exit_text,
            exit_type,
            connecting_area,
            connecting_room,
            active
        ) VALUES (?,?,?,?,?,?,?);
        """

    # insert rooms_general information
    await db.execute(query_insert_rooms_general, (
        'test',
        1,
        'Old House, Living Room',
        'The room is lightly lit in three of its four corners.  In the center of the room sits a square wooden coffee table with craft material and general knick-knacks.  Bordering two sides of the coffee table is a shabby L-shaped couch with a kind lady laying down stroking the back of a napping dog.'
        ))
    await db.execute(query_insert_rooms_general, ('test', 2, 'Old House, Hallway', 'Room 2 Description'))
    await db.execute(query_insert_rooms_general, ('test', 3, 'Old House, Dining Room', 'Room 3 Description'))
    await db.commit()

    # insert rooms_connections information
    await db.execute(query_insert_rooms_connections, ('test', 1, 'North', 'n', 'test', 2, 1))
    await db.execute(query_insert_rooms_connections, ('test', 1, 'South', 's', 'test', 3, 1))
    await db.execute(query_insert_rooms_connections, ('test', 2, 'South', 's', 'test', 1, 1))
    await db.execute(query_insert_rooms_connections, ('test', 3, 'North', 'n', 'test', 1, 1))
    await db.commit()

async def main():
    db_connection = 'test.db'

    async with aiosqlite.connect(db_connection) as db:
        await table_create_users(db)
        await table_create_rooms_general(db)
        await table_create_rooms_connections(db)
        await table_create_rooms_switches(db)
        await insert_test_users(db)
        await insert_test_rooms(db)

if __name__ == '__main__':
    asyncio.run(main())