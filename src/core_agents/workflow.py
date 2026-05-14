import os
import ast
import json
from langgraph.graph import StateGraph, END
from .state import MigrationState
from .models import ModelFactory
from .schemas import TranslatedCodeOutput

# ==========================================
# 1. THE AGENTS (Nodes)
# ==========================================

def context_agent(state: MigrationState):
    """
    The Eyes: Reads the actual file from disk.
    In a Tier-1 system, this would also fetch 'Related Files' 
    found by our Tree-sitter parser for better AI context.
    """
    print(f"  [Context Agent] Loading source: {state['file_path']}")
    
    try:
        with open(state['file_path'], 'r', encoding='utf-8') as f:
            content = f.read()
        return {"legacy_code": content, "migration_notes": []}
    except Exception as e:
        return {"error_message": f"Could not read file: {str(e)}"}

def translation_agent(state: MigrationState):
    """
    The Brain: Uses the Model Factory to translate.
    (This is the logic we refined in the previous step).
    """
    print(f"  [Translation Agent] Translating via {state['model_choice']}...")
    
    error_context = f"\nFIX PREVIOUS ERROR: {state['error_message']}" if state['error_message'] else ""
    
    prompt = f"""
    Target Stack: {state['target_stack']}
    User Preferences: {state['custom_instructions']}
    {error_context}

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

        return {
            "translated_code": translated_code, 
            "retry_count": state['retry_count'] + 1,
            "error_message": None
        }
    except Exception as e:
        return {"error_message": f"AI Error: {str(e)}", "retry_count": state['retry_count'] + 1}

def validation_agent(state: MigrationState):
    """The Hands: Validates syntax and writes to disk."""
    print(f"  [Validation Agent] Checking {state['target_stack']} syntax...")
    
    # --- THE GUARD CLAUSE (BUG FIX) ---
    # If the translator failed, abort validation immediately!
    if state.get("error_message"):
        print(f"  [Validation Agent] ❌ Bypassing validation due to earlier error.")
        return {"error_message": state["error_message"]}

    # Default to empty string if somehow None
    code = state.get("translated_code") or ""

    # Basic Python Syntax Check (if target is Python)
    if "python" in state['target_stack'].lower():
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {"error_message": f"Syntax Error: {str(e)}"}

    # Success Path: Write file
    output_path = state['file_path'].replace("legacy_codebase", "modernized_codebase")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(code)

    note = f"Migrated {os.path.basename(state['file_path'])} to {state['target_stack']}."
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

    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {"retry": "translator", "end": END}
    )

    return workflow.compile()

migration_swarm = build_migration_graph()