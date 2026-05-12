import aiosqlite

DB = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            banned INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            admin_msg_id INTEGER,
            user_id INTEGER
        )
        """)

        await db.commit()


async def add_user(user):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        INSERT OR IGNORE INTO users(id, username, full_name)
        VALUES (?, ?, ?)
        """, (
            user.id,
            user.username,
            user.full_name
        ))
        await db.commit()


async def save_message(admin_msg_id, user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        INSERT INTO messages(admin_msg_id, user_id)
        VALUES (?, ?)
        """, (admin_msg_id, user_id))
        await db.commit()


async def get_user(admin_msg_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("""
        SELECT user_id FROM messages
        WHERE admin_msg_id=?
        """, (admin_msg_id,)) as cur:

            row = await cur.fetchone()
            return row[0] if row else None


async def ban(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        UPDATE users SET banned=1
        WHERE id=?
        """, (user_id,))
        await db.commit()


async def unban(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        UPDATE users SET banned=0
        WHERE id=?
        """, (user_id,))
        await db.commit()


async def is_banned(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("""
        SELECT banned FROM users
        WHERE id=?
        """, (user_id,)) as cur:

            row = await cur.fetchone()
            return row and row[0] == 1


async def get_banned():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("""
        SELECT id, username, full_name
        FROM users
        WHERE banned=1
        """) as cur:

            return await cur.fetchall()