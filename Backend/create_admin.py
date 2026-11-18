from werkzeug.security import generate_password_hash
from database import get_connection, create_admins_table


create_admins_table()

connection = get_connection()
cursor = connection.cursor()


name = input("Enter admin name: ").strip()
email = input("Enter admin email: ").strip().lower()
password = input("Enter admin password: ")


password_hash = generate_password_hash(password)


try:

    cursor.execute("""
        INSERT INTO admins
        (name, email, password_hash)
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        password_hash
    ))

    connection.commit()

    print()
    print("================================")
    print("ADMIN CREATED SUCCESSFULLY")
    print("================================")
    print("Name:", name)
    print("Email:", email)

except Exception as e:

    print()
    print("Could not create admin.")
    print("Error:", e)

finally:

    connection.close()