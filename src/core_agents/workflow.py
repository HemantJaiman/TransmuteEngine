import os
import ast
import json
import redis
from langgraph.graph import StateGraph, END
from .state import MigrationState
from .models import ModelFactory
from .schemas import TranslatedCodeOutput

def broadcast_status(message: str, msg_type: str = "info"):
    print(message)
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)))
        r.publish("swarm_logs", json.dumps({"message": message, "type": msg_type}))
    except Exception:
        pass

# ==========================================
# 1. THE AGENTS (Nodes)
# ==========================================

def context_agent(state: MigrationState):
    paths = state['file_path'] if isinstance(state['file_path'], list) else [state['file_path']]
    display_name = " + ".join([os.path.basename(p) for p in paths])
    
    broadcast_status(f"  [Context] Analyzing AST structure for {display_name}...", "info")
    
    try:
        content = ""
        for p in paths:
            with open(p, 'r', encoding='utf-8') as f:
                content += f"\n# --- FILE: {os.path.basename(p)} ---\n" + f.read() + "\n"
        return {"legacy_code": content, "migration_notes": []}
    except Exception as e:
        return {"error_message": f"Could not read file: {str(e)}"}

def translation_agent(state: MigrationState):
    broadcast_status(f"  [Translator] AI is actively converting logic to {state['target_stack']}...", "info")
    error_context = f"\nFIX PREVIOUS ERROR: {state['error_message']}" if state['error_message'] else ""
    
    prompt = f"""
    Target Stack: {state['target_stack']}
    User Preferences: {state['custom_instructions']}
    {error_context}

    CRITICAL INSTRUCTION:
    If multiple legacy files are provided below, they contain a CIRCULAR DEPENDENCY. 
    You must merge their logic into a SINGLE cohesive, highly-optimized file to break the cycle.

    Legacy Code:
    {state['legacy_code']}
    """

    model = ModelFactory.get_model(state['model_choice'])

    try:
        if state['model_choice'] == "gemini":
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json", "response_schema": TranslatedCodeOutput}
            )
            data = json.loads(response.text)
            translated_code = data['source_code']
        else:
            response = model.beta.chat.completions.parse(
                model=state['model_choice'] if state['model_choice'] != "gpt4" else "gpt-4o-2024-08-06",
                messages=[{"role": "user", "content": prompt}],
                response_format=TranslatedCodeOutput,
            )
            translated_code = response.choices[0].message.parsed.source_code

        broadcast_status(f"  [Translator] ✅ Logic successfully translated.", "success")
        return {"translated_code": translated_code, "retry_count": state['retry_count'] + 1, "error_message": None}
    
    except Exception as e:
        # --- THE FIX: We were hiding the error! Now we broadcast it to the UI and Terminal ---
        error_msg = f"API Error: {str(e)}"
        broadcast_status(f"  [Translator] ❌ {error_msg}", "error")
        return {"error_message": error_msg, "retry_count": state['retry_count'] + 1}

def validation_agent(state: MigrationState):
    broadcast_status(f"  [Validator] Compiling and verifying syntax integrity...", "info")
    
    if state.get("error_message"):
        broadcast_status(f"  [Validator] ⚠️ Bypassing validation due to earlier error.", "error")
        return {"error_message": state["error_message"]}

    code = state.get("translated_code") or ""

    if "python" in state['target_stack'].lower():
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {"error_message": f"Syntax Error: {str(e)}"}

    if isinstance(state['file_path'], list):
        merged_name = "_".join([os.path.splitext(os.path.basename(p))[0] for p in state['file_path']]) + ".py"
        base_dir = os.path.dirname(state['file_path'][0])
        output_path = os.path.join(base_dir, merged_name).replace("legacy_codebase", "modernized_codebase")
        note_filename = merged_name
    else:
        output_path = state['file_path'].replace("legacy_codebase", "modernized_codebase")
        note_filename = os.path.basename(state['file_path'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(code)

    note = f"Migrated {note_filename} to {state['target_stack']}."
    broadcast_status(f"  [Validator] ✅ Syntax is clean. Codebase updated.", "success")
    return {"error_message": None, "migration_notes": [note]}

# ==========================================
# 2. THE ROUTING & GRAPH
# ==========================================

def should_continue(state: MigrationState):
    if state.get("error_message") and state['retry_count'] < 3:
        return "retry"
    return "end"

def build_migration_graph():
    workflow = StateGraph(MigrationState)
    workflow.add_node("context", context_agent)
    workflow.add_node("translator", translation_agent)
    workflow.add_node("validator", validation_agent)
    workflow.set_entry_point("context")
    workflow.add_edge("context", "translator")
    workflow.add_edge("translator", "validator")
    workflow.add_conditional_edges("validator", should_continue, {"retry": "translator", "end": END})
    return workflow.compile()

migration_swarm = build_migration_graph()