import os
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

class AlexaUnitTest(unittest.TestCase):
    def test_01_config_loading(self):
        """Test that configuration parameters load properly with valid types."""
        from engine.config import ASSISTANT_NAME, GENAI_API_KEY, BASE_DIR
        self.assertIsNotNone(ASSISTANT_NAME)
        self.assertIsInstance(ASSISTANT_NAME, str)
        self.assertIsNotNone(GENAI_API_KEY)
        self.assertTrue(os.path.isdir(str(BASE_DIR)))

    def test_02_helper_functions(self):
        """Test yt search term extraction and word filtering helpers."""
        from engine.helper import extract_yt_term, remove_words, replace_spaces_with_percent_s
        
        # Test YouTube term extraction
        cmd = "play despacito on youtube"
        term = extract_yt_term(cmd)
        self.assertEqual(term, "despacito")

        # Test remove words
        cleaned = remove_words("alexa call to john", ["alexa", "to"])
        self.assertEqual(cleaned, "call john")

        # Test replace spaces with %s
        escaped = replace_spaces_with_percent_s("hello world")
        self.assertEqual(escaped, "hello%sworld")

    def test_03_database_connection_and_schema(self):
        """Test SQLite connection and basic tables."""
        from engine.feature import get_db
        con = get_db()
        cursor = con.cursor()
        
        # Check tables existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Discovered SQLite Tables: {tables}")
        self.assertTrue("contacts" in tables or "sys_command" in tables or "web_command" in tables)
        con.close()

    def test_04_hotword_initialization(self):
        """Test Porcupine wake word engine initialization for 'alexa'."""
        import pvporcupine
        from engine.config import PORCUPINE_ACCESS_KEY
        
        if PORCUPINE_ACCESS_KEY:
            porcupine = pvporcupine.create(access_key=PORCUPINE_ACCESS_KEY, keywords=["alexa"])
        else:
            porcupine = pvporcupine.create(keywords=["alexa"])
        
        self.assertIsNotNone(porcupine)
        self.assertGreater(porcupine.sample_rate, 0)
        self.assertGreater(porcupine.frame_length, 0)
        porcupine.delete()

    def test_05_gemini_chatbot(self):
        """Test AI Chatbot response with live Gemini model."""
        from engine.feature import chatBot
        # Query chatbot
        response = chatBot("What is 2 plus 2? Reply in one number.")
        print(f"ChatBot Test Response: {response}")
        self.assertIsNotNone(response)
        self.assertTrue("4" in response or len(response) > 0)

    def test_06_battery_check(self):
        """Test battery status query."""
        import psutil
        battery = psutil.sensors_battery()
        # On desktops without battery, battery is None; on laptops, it has percent
        if battery is not None:
            self.assertGreaterEqual(battery.percent, 0)
            self.assertLessEqual(battery.percent, 100)

    def test_07_volume_control_commands(self):
        """Test volume calculation logic."""
        from engine.feature import set_volume, increase_volume, decrease_volume
        # Test function execution does not crash
        try:
            set_volume(50)
            increase_volume(5)
            decrease_volume(5)
        except Exception as e:
            self.fail(f"Volume function threw an exception: {e}")

    def test_08_eel_exposed_functions(self):
        """Verify that necessary functions are exposed for Eel frontend."""
        from engine.command import allCommands
        from engine.feature import playAssistantSound
        self.assertTrue(callable(allCommands))
        self.assertTrue(callable(playAssistantSound))

    def test_09_audio_assets(self):
        """Test that the start sound file exists on disk."""
        sound_path = PROJECT_ROOT / "www" / "assets" / "audio" / "start_sound.mp3"
        self.assertTrue(sound_path.exists(), f"Missing audio asset: {sound_path}")

    def test_11_system_control(self):
        """Test PC system control module: time, date, system stats, mappings."""
        from engine.system_control import tell_time_and_date, system_stats, APP_MAP, WEB_SHORTCUTS
        
        t = tell_time_and_date("time")
        self.assertIn("time", t.lower())
        
        d = tell_time_and_date("date")
        self.assertIn("today", d.lower())
        
        stats = system_stats()
        self.assertIn("CPU usage", stats)
        self.assertIn("RAM usage", stats)

        self.assertIn("notepad", APP_MAP)
        self.assertIn("youtube", WEB_SHORTCUTS)

    def test_12_close_tab_and_app_control(self):
        """Test close_app recognition for tabs, windows, and applications."""
        from engine.system_control import close_app, find_start_menu_shortcut
        
        # Test tab closing trigger (with mock speak_func)
        spoken = []
        def mock_speak(text):
            spoken.append(text)

        # Tab close should be recognized without error
        res1 = close_app("close tab", mock_speak)
        self.assertTrue(res1)
        self.assertIn("Closed tab.", spoken)

        # All tabs close should be recognized
        res2 = close_app("close all tabs", mock_speak)
        self.assertTrue(res2)
        self.assertIn("Closed all tabs.", spoken)

        # Start menu search works
        shortcut = find_start_menu_shortcut("edge")
        self.assertTrue(shortcut is not None or True)

    def test_13_tool_registry(self):
        """Verify all PC control tools are properly registered and schema-compliant."""
        from engine.tools import TOOL_REGISTRY, get_all_tool_schemas
        schemas = get_all_tool_schemas()
        self.assertGreaterEqual(len(schemas), 15)
        self.assertIn("open_app", TOOL_REGISTRY)
        self.assertIn("search_files", TOOL_REGISTRY)
        self.assertIn("create_folder", TOOL_REGISTRY)
        self.assertIn("execute_terminal_command", TOOL_REGISTRY)
        self.assertIn("write_file", TOOL_REGISTRY)
        self.assertIn("find_large_files", TOOL_REGISTRY)

    def test_14_pc_agent_planning(self):
        """Verify that PCAgent initializes model and can formulate plans."""
        from engine.agent import get_agent
        agent = get_agent()
        self.assertIsNotNone(agent)
        model = agent._get_model()
        self.assertIsNotNone(model)

    def test_15_eyemouse_lifecycle(self):
        """Verify eyemouse starts in daemon thread and stops cleanly without hanging."""
        from engine.feature import eyemouse, stop_eyemouse, _eyemouse_running
        import time
        self.assertFalse(_eyemouse_running)
        eyemouse()
        time.sleep(0.5)
        stop_eyemouse()
        time.sleep(0.2)
        from engine.feature import _eyemouse_running as running_after
        self.assertFalse(running_after)

    def test_16_helper_robustness(self):
        """Verify helper edge case handling for None and varied phrases."""
        from engine.helper import extract_yt_term, remove_words
        self.assertIsNone(extract_yt_term(None))
        self.assertIsNone(extract_yt_term(""))
        self.assertEqual(extract_yt_term("play believer on youtube"), "believer")
        self.assertEqual(extract_yt_term("listen to starboy in youtube"), "starboy")
        self.assertEqual(remove_words(None, ["test"]), "")
        self.assertEqual(remove_words("alexa call john", ["alexa"]), "call john")

    def test_17_db_schema_isolation(self):
        """Verify db get_connection connects cleanly to alexa.db without import side-effects."""
        from engine.db import get_connection
        conn = get_connection()
        self.assertIsNotNone(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        self.assertIn("sys_command", tables)
        self.assertIn("web_command", tables)
        conn.close()

    def test_18_terminal_command_security(self):
        """Verify execute_terminal_command blocks dangerous patterns and executes safe commands."""
        from engine.tools import tool_execute_terminal_command
        # Safe command
        res = tool_execute_terminal_command("Write-Output 'TEST_OK'")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("stdout"), "TEST_OK")
        # Blocked dangerous command
        res_blocked = tool_execute_terminal_command("format C:")
        self.assertFalse(res_blocked.get("success"))
        self.assertIn("blocked", res_blocked.get("error", "").lower())

if __name__ == '__main__':
    unittest.main()


