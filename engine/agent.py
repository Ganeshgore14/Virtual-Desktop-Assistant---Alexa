import os
import re
import json
import time
import traceback
from pathlib import Path

import eel

from engine.config import ASSISTANT_NAME, GENAI_API_KEY
from engine.command import speak
from engine.tools import TOOL_REGISTRY, get_all_tool_schemas

# Active execution state
_is_cancelled = False

def cancel_current_task():
    global _is_cancelled
    _is_cancelled = True

def is_task_cancelled():
    global _is_cancelled
    return _is_cancelled

class PCAgent:
    """
    Autonomous Windows PC Control Agent.
    Implements the 7-phase agent loop:
    UNDERSTAND REQUEST → PLAN → SELECT TOOLS → CHECK PERMISSIONS → EXECUTE → VERIFY → RESPOND
    """

    def __init__(self):
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]
        self._configure_genai()

    def _configure_genai(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=GENAI_API_KEY, transport='rest')
            self.genai = genai
        except Exception as e:
            print(f"GenAI configuration error: {e}")
            self.genai = None

    def _get_model(self):
        if not self.genai:
            self._configure_genai()
        if not self.genai:
            return None

        for model_name in self.candidate_models:
            try:
                return self.genai.GenerativeModel(model_name)
            except Exception:
                continue
        return None

    def _build_planning_prompt(self, user_request: str) -> str:
        schemas = get_all_tool_schemas()
        schemas_json = json.dumps(schemas, indent=2)

        desktop = str(Path.home() / "Desktop")
        documents = str(Path.home() / "Documents")
        downloads = str(Path.home() / "Downloads")

        active_window_text = "Unknown"
        active_process = "Unknown"
        if "get_active_window_info" in TOOL_REGISTRY:
            try:
                winfo = TOOL_REGISTRY["get_active_window_info"].func()
                active_window_text = winfo.get("window_title") or "Desktop / Background"
                active_process = winfo.get("process_name") or "System"
            except Exception:
                pass

        prompt = f"""You are {ASSISTANT_NAME}, an autonomous Windows PC Control AI Agent with full access to the user's computer through registered tools.

USER REQUEST: "{user_request}"

SYSTEM ENVIRONMENT:
- OS: Windows 10/11
- Desktop Path: {desktop}
- Documents Path: {documents}
- Downloads Path: {downloads}

ACTIVE FOREGROUND CONTEXT:
- Currently Active Window Title: "{active_window_text}"
- Currently Focused Application: "{active_process}"

AVAILABLE TOOLS:
{schemas_json}

YOUR TASK:
Analyze the user's natural language request. Decide if this requires one or multiple tool executions.
Follow this loop: UNDERSTAND REQUEST -> PLAN -> SELECT TOOLS -> CHECK PERMISSIONS -> EXECUTE -> VERIFY -> RESPOND.

RULES:
1. If the request is purely informational/conversational and needs no computer actions, return empty actions: "actions": [].
2. For PC tasks (e.g. opening apps, organizing files, running scripts, searching files, controlling windows, taking notes, creating folders, running terminal commands), plan the exact sequence of tools needed.
3. For tasks asking about the current window or active tab (e.g. "summarize this page", "what's on my screen", "explain this code", "what tab is this"):
   - Use 'analyze_current_window_or_tab' to visually read and summarize the active tab/screen content.
   - Use 'interact_with_current_tab' for browser tab interactions (refresh, new tab, bookmark, scroll).
   - Use 'close_tab' to close the active tab.
4. Validate tool names and arguments against the provided schemas.
5. If a task requires multiple steps (e.g., "Create a folder on Desktop, then save a report in it, then open it in Notepad"), list all required actions in execution order.
6. Never pretend an action was executed if no tool exists for it.
7. Return ONLY a single raw JSON object without markdown formatting or code blocks.

JSON SCHEMA:
{{
  "thought": "Your internal chain-of-thought analysis of what needs to be done",
  "plan": ["step 1 description", "step 2 description"],
  "actions": [
    {{
      "tool": "exact_tool_name_from_registry",
      "args": {{"arg_name": "arg_value"}}
    }}
  ],
  "spoken_summary_template": "A concise 1-2 sentence spoken summary for the user once all steps complete successfully."
}}
"""
        return prompt

    def run(self, user_request: str) -> str:
        """
        Executes the autonomous agent loop for a user request.
        """
        global _is_cancelled
        _is_cancelled = False

        print(f"\n[Agent] Phase 1: Understanding Request: '{user_request}'")
        try:
            eel.DisplayMessage("Thinking & planning...")
        except Exception:
            pass

        model = self._get_model()
        if not model:
            msg = "AI engine is currently unavailable. Please check your internet connection or API key."
            speak(msg)
            return msg

        # Phase 2 & 3: PLAN & SELECT TOOLS
        prompt = self._build_planning_prompt(user_request)
        plan_data = None

        try:
            response = model.generate_content(prompt)
            if response and response.text:
                raw_text = response.text.strip()
                # Clean any markdown code fences if present
                clean_json = re.sub(r'^```(json)?\s*', '', raw_text, flags=re.MULTILINE)
                clean_json = re.sub(r'```$', '', clean_json, flags=re.MULTILINE).strip()
                plan_data = json.loads(clean_json)
        except Exception as e:
            print(f"[Agent] Planning error: {e}")
            traceback.print_exc()

        if not plan_data or not isinstance(plan_data, dict):
            # Fallback to direct conversational answer
            print("[Agent] Falling back to direct conversational response")
            try:
                resp = model.generate_content(
                    f"You are {ASSISTANT_NAME}, a helpful Windows voice assistant. Reply to the user concisely in 1-2 friendly sentences. User: {user_request}"
                )
                text = resp.text.replace("*", "").replace("#", "").strip() if resp else "I couldn't process that request."
                speak(text)
                return text
            except Exception as e:
                speak("I encountered an issue processing your request.")
                return str(e)

        actions = plan_data.get("actions", [])
        thought = plan_data.get("thought", "")
        plan_steps = plan_data.get("plan", [])
        summary_template = plan_data.get("spoken_summary_template", "")

        print(f"[Agent] Plan: {plan_steps}")
        print(f"[Agent] Actions count: {len(actions)}")

        # If conversational only (no actions needed)
        if not actions:
            if summary_template:
                speak(summary_template)
                return summary_template
            fallback_text = thought if thought else "Done."
            speak(fallback_text)
            return fallback_text

        # Phase 4, 5, 6: CHECK PERMISSIONS -> EXECUTE -> VERIFY
        execution_results = []
        for i, action in enumerate(actions):
            if is_task_cancelled():
                speak("Task cancelled.")
                return "Task cancelled by user."

            tool_name = action.get("tool")
            args = action.get("args", {})

            if tool_name not in TOOL_REGISTRY:
                print(f"[Agent] Unknown tool requested: {tool_name}")
                continue

            tool = TOOL_REGISTRY[tool_name]
            step_desc = plan_steps[i] if i < len(plan_steps) else f"Running {tool_name}"
            print(f"\n[Agent] Step {i+1}/{len(actions)}: {step_desc} (Tool: {tool_name}, Tier: {tool.tier})")

            try:
                eel.DisplayMessage(f"{step_desc}...")
            except Exception:
                pass

            # Phase 4: CHECK PERMISSIONS
            if tool.tier == "DESTRUCTIVE":
                print(f"[Agent] Warning: Executing Tier 3 Destructive tool: {tool_name}")

            # Phase 5: EXECUTE TOOL
            try:
                start_t = time.time()
                result = tool.func(**args)
                elapsed = round(time.time() - start_t, 2)
                print(f"[Agent] Tool {tool_name} returned in {elapsed}s: {result}")
            except Exception as ex:
                result = {"success": False, "error": str(ex)}
                print(f"[Agent] Tool {tool_name} raised exception: {ex}")

            # Phase 6: VERIFY RESULT
            if not result.get("success", False):
                err = result.get("error", "Unknown error")
                print(f"[Agent] Step failed: {err}. Attempting self-correction...")

                # Self-Correction Diagnosis with Gemini
                diag_prompt = f"""A step in an automated Windows PC task failed.
Original user request: "{user_request}"
Failed Tool: {tool_name} with arguments {json.dumps(args)}
Error message: "{err}"

Provide a single alternative action or safe fix using one of the available tools:
{json.dumps(get_all_tool_schemas())}

Return JSON:
{{
  "retry": true,
  "action": {{"tool": "tool_name", "args": {{}}}}
}}
"""
                try:
                    fix_resp = model.generate_content(diag_prompt)
                    if fix_resp and fix_resp.text:
                        fix_json = re.sub(r'^```(json)?\s*', '', fix_resp.text.strip(), flags=re.MULTILINE)
                        fix_json = re.sub(r'```$', '', fix_json, flags=re.MULTILINE).strip()
                        fix_data = json.loads(fix_json)
                        if fix_data.get("retry") and "action" in fix_data:
                            alt_tool_name = fix_data["action"].get("tool")
                            alt_args = fix_data["action"].get("args", {})
                            if alt_tool_name in TOOL_REGISTRY:
                                print(f"[Agent] Retrying with alternative tool: {alt_tool_name}")
                                result = TOOL_REGISTRY[alt_tool_name].func(**alt_args)
                except Exception as diag_ex:
                    print(f"[Agent] Self-correction failed: {diag_ex}")

            execution_results.append({
                "step": step_desc,
                "tool": tool_name,
                "result": result
            })

        # Phase 7: RESPOND
        # Synthesize final natural language completion summary
        successful_steps = [r for r in execution_results if r["result"].get("success", False)]
        failed_steps = [r for r in execution_results if not r["result"].get("success", False)]

        if failed_steps and not successful_steps:
            first_err = failed_steps[0]["result"].get("error", "Action could not be completed.")
            final_spoken = f"I ran into an issue: {first_err}"
        elif summary_template:
            final_spoken = summary_template
        elif successful_steps:
            final_spoken = f"Completed: {', '.join([s['step'] for s in successful_steps])}."
        else:
            final_spoken = "The task has been completed."

        print(f"\n[Agent] Phase 7: Final Spoken Response: '{final_spoken}'")
        speak(final_spoken)
        return final_spoken

# Global Singleton Agent Instance
_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PCAgent()
    return _agent_instance
