import asyncpg
import asyncio

# Hàm kết nối đến PostgreSQL
async def connect_to_db():
    connection_string = "postgresql+asyncpg://postgres:example@localhost:5432/data"
    
    try:
        # Kết nối đến cơ sở dữ liệu PostgreSQL
        conn = await asyncpg.connect(connection_string)
        print("Kết nối thành công tới database!")

        # Ví dụ truy vấn đọc dữ liệu từ bảng users
        users = await conn.fetch("SELECT * FROM publics.users;") 
        for user in users:
            print(user)

        # Đóng kết nối
        await conn.close()
        print("Đã đóng kết nối.")
    
    except Exception as e:
        print(f"Lỗi khi kết nối: {e}")

# Chạy hàm kết nối
if __name__ == "__main__":
    asyncio.run(connect_to_db())
