import json 
import sqlite3
from .config import Config
from .analyser import ContextAnalyser

class Memory:
    """
    Memory class to handle memory operations using SQLite.

    Manages tables: 
    - memory: stores the role and data for each message. This is tyhe full original history of the conversation.
    - user_profile: stores the user profile data. It is data extracted from the conversation using LLM. It is only most relevant data about the user, like the name
    - key_topics: stores the key topics of the conversation. It is data extracted from the conversation using LLM. Topic and count of mentions
    - summary: stores the summary of the conversation. It is the one row table
    """
    def __init__(self, config: Config):
        """
        Initialize the Memory class with a Config object.
        
        Args:
            config (Config): Configuration object containing database file path and other settings.
        """
        self.config = config
        self.conn = sqlite3.connect(self.config.database_file_path)
        self._create_tables()

    def __del__(self):
        """ Close the database connection when the object is deleted. """
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        """Create tables if they do not exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    data TEXT NOT NULL,
                    analysed INTEGER DEFAULT 0
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT NOT NULL PRIMARY KEY,
                    data TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS key_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    count INTEGER NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference TEXT NOT NULL,
                    summary TEXT NOT NULL
                )
            """)

    def history_dump(self):
        """ Returns the history of the memory. All messages stored in teh DB

        Returns:
            generator: A generator that yields each message in the memory.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, role, data FROM memory")
        rows = cursor.fetchall()

        for row in rows:
            row_id, role, content = row
            yield f"{row_id}: {role}: {content}"
        cursor.close()

    def get_number_of_messages_awaiting_for_analysis(self) -> int:
        """ Returns the number of messages in the memory table that are not analysed yet. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memory WHERE analysed = 0")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def remember(self, role: str, contents: list | dict | str) -> None:
        """
        Store new data in the memory table.
        Args:
            role (str): The role of the message (e.g., "user", "assistant").
            contents (list | dict | str): The content of the message to be stored.
        """
        data = json.dumps(contents)
        with self.conn:
            self.conn.execute(
                "INSERT INTO memory (role, data, analysed) VALUES (?, ?, 0)",
                (role, data)
            )

    def recall(self) -> str:
        """
        Recall the memory and return the user profile, key topics, and summary.
        Returns:
            str: A string containing the user profile, key topics, and summary.
        """
        current_profile = self.__get_user_profile_info()
        current_key_topics = self.__get_key_topics()
        summary = self.__get_summary()

        if len(current_profile) == 0 and len(current_key_topics) == 0 and len(summary) == 0:
            return None

        all_info = f"User profile:\n{current_profile}\n\nKey topics:\n{current_key_topics}\n\nSummary:\n{summary}\n\n"

        return all_info

    def search(self, data: str) -> str:
        """
        Search for a specific data in the memory table and return surrounding entries.
        Args:
            data (str): The data to search for in the memory.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, role, data FROM memory")
        rows = cursor.fetchall()

        # Search for match and return surrounding entries
        for i, (row_id, role, content) in enumerate(rows):
            if data in content:
                start = max(0, i - 5)
                end = min(len(rows), i + 6)
                return '\n'.join(
                    f"{rows[j][1]}: {rows[j][2]}" for j in range(start, end)
                )
        return ''
    
    def clear(self) -> None:
        """ Clear all data from the memory tables. """
        with self.conn:
            self.conn.execute("DELETE FROM memory")
            self.conn.execute("DELETE FROM user_profile")
            self.conn.execute("DELETE FROM key_topics")
            self.conn.execute("DELETE FROM summary")
            self.conn.commit()
            self.conn.execute("VACUUM")
            self.conn.commit()

    def patch_memories_if_new_data(self):
        """ Check if there is new data in the memory table and patch it. """
        print("Checking for new data in the memory table...")
        if self.get_number_of_messages_awaiting_for_analysis() > self.config.auto_patch_when_num_of_messages_is_greater_then:
            print("Found new data in the memory table. Patching...")
            result = self.patch_memories()
            print(result)

    def patch_memories(self) -> str:
        """ Extract data not analysed from the memory table and store it in the user_profile and key_topics tables. 
        This is the main function that will be called to create the memories.
        It will extract the user profile, key topics and summary from the memory table and store it in the user_profile, key_topics and summary tables.
        """

        analyser = ContextAnalyser(self.config)

        current_profile = self.__get_user_profile_info()
        current_key_topics = self.__get_key_topics()
        summary = self.__get_summary()

        full_history = ""

        result_log = ""

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, role, data FROM memory WHERE analysed = 0")
        rows = cursor.fetchall()

        result_log += f"Found {len(rows)} unanalysed rows in the memory table.\n"

        for row in rows:
            row_id, role, content = row

            # TODO:
            if role == "user":
                current_profile = analyser.extract_user_profile_info(content, current_profile)

            full_history += f"{role}: {content}\n\n"

            if len(full_history) > self.config.summarizer_request_max_length:
                current_key_topics = analyser.extract_key_topics(full_history, current_key_topics)
                summary = analyser.extract_summary(full_history, summary)
                full_history = ""

            # update the analysed field to 1
            cursor.execute("UPDATE memory SET analysed = 1 WHERE id = ?", (row_id,))
            self.conn.commit()
        cursor.close()

        if len(full_history) > 0:
            current_key_topics = analyser.extract_key_topics(full_history, current_key_topics)
            summary = analyser.extract_summary(full_history, summary)

        # Sync the user profile with the database
        if self.__sync_user_profile(current_profile):
            result_log += "User profile updated.\n"

        # Sync the key topics with the database
        if self.__sync_key_topics(current_key_topics):
            result_log += "Key topics updated.\n"

        # Sync the summary with the database
        if self.__sync_summary(summary):
            result_log += "Summary updated.\n"

        return result_log
    
    def __get_user_profile_info(self) -> dict:
        """ Load current user profile data from the database. """ 
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, data FROM user_profile")
        rows = cursor.fetchall()
        user_profile = {}
        for row in rows:
            key, data = row
            user_profile[key] = json.loads(data)
        return user_profile
    
    def __get_key_topics(self) -> dict:
        """ Load current key topics data from the database. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT topic, count FROM key_topics")
        rows = cursor.fetchall()
        key_topics = {}
        for row in rows:
            topic, count = row
            key_topics[topic] = count
        return key_topics
    
    def __get_summary(self) -> str:
        """ Load current summary data from the database. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT summary FROM summary")
        row = cursor.fetchone()
        if row:
            return row[0]
        return ""
    
    def __sync_user_profile(self, user_profile: dict) -> bool:
        """ Sync the user profile data with the database. """
        current_profile = self.__get_user_profile_info()

        # if identical - do nothing
        if current_profile == user_profile:
            return False

        cursor = self.conn.cursor()
        for key, data in user_profile.items():
            cursor.execute("INSERT OR REPLACE INTO user_profile (key, data) VALUES (?, ?)", (key, json.dumps(data)))
            if key in current_profile:
                del current_profile[key] 
        self.conn.commit()

        # Remove keys that are not in the new profile
        for key in current_profile.keys():
            cursor.execute("DELETE FROM user_profile WHERE key = ?", (key,))
            self.conn.commit()

        return True

    def __sync_key_topics(self, key_topics: dict) -> bool:
        """ Sync the key topics data with the database. """
        current_key_topics = self.__get_key_topics()

        # if identical - do nothing
        if current_key_topics == key_topics:
            return False

        cursor = self.conn.cursor()
        for topic, count in key_topics.items():
            cursor.execute("INSERT OR REPLACE INTO key_topics (topic, count) VALUES (?, ?)", (topic, count))
            if topic in current_key_topics:
                del current_key_topics[topic]
        self.conn.commit()

        # Remove keys that are not in the new profile
        for topic in current_key_topics.keys():
            cursor.execute("DELETE FROM key_topics WHERE topic = ?", (topic,))
            self.conn.commit()

        return True

    def __sync_summary(self, summary: str) -> bool:
        """ Sync the summary data with the database. """
        current_summary = self.__get_summary()
        # if identical - do nothing
        if current_summary == summary:
            return False
        print(f"Summary: {summary}")
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO summary (reference,summary) VALUES (?,?)", ("", summary))
        self.conn.commit()

        return True
        
    def rebuild_memories(self) -> None:
        """ Rebuild the memories from the memory table. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, role, data FROM memory")
        rows = cursor.fetchall()

        for row in rows:
            row_id, role, content = row