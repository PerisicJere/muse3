import mysql.connector
import json

def onDeleteUserTrigger(user_id):
    try:
        with open("connectorConfig.json", "r") as f:
            config = json.load(f)
        connection_config = config["mysql"]
        connection = mysql.connector.connect(**connection_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("DROP TRIGGER IF EXISTS delete_reviews")
        # Create trigger
        create_trigger_query = """
        CREATE TRIGGER delete_reviews
        BEFORE DELETE ON user
        FOR EACH ROW
        BEGIN
            DELETE FROM review WHERE user_id = OLD.user_id;
        END
        """
        cursor.execute(create_trigger_query)

        # Execute the DELETE statement for the user and let the trigger handle reviews
        delete_user_query = f"DELETE FROM user WHERE user_id = {user_id}"
        cursor.execute(delete_user_query)

        # Commit the changes
        connection.commit()

        print(f"User with ID {user_id} and associated reviews deleted successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

        if 'connection' in locals() and connection.is_connected():
            connection.close()



onDeleteUserTrigger(198)