import os
# pyrefly: ignore [missing-import]
from ingestion.graph import DependencyGraph

def create_dummy_legacy_repo():
    """Creates a fake legacy folder with REAL Python imports to test our AST."""
    os.makedirs("legacy_codebase", exist_ok=True)
    
    # 1. The Database file (Depends on nothing)
    with open("legacy_codebase/database.py", "w") as f:
        f.write("def connect():\n    return 'connected'\n")

    # 2. The Auth file (IMPORTS database)
    with open("legacy_codebase/auth.py", "w") as f:
        f.write("import database\n\ndef login():\n    database.connect()\n")

    # 3. The API Server (IMPORTS auth)
    with open("legacy_codebase/api.py", "w") as f:
        f.write("from auth import login\n\ndef route():\n    login()\n")

def run_test():
    print("🚀 Initializing Transmute Engine Test...")
    create_dummy_legacy_repo()
    
    # Initialize our graph engine on the fake codebase
    engine = DependencyGraph("legacy_codebase")
    engine.build_graph()
    
    print("\n📊 Calculating Migration Order via Topological Sort...")
    order = engine.get_migration_order()
    
    print("\n✅ AI Swarm Execution Order:")
    for step, file_path in enumerate(order, 1):
        filename = os.path.basename(file_path)
        print(f"  Step {step}: Send [{filename}] to the AI Swarm.")

if __name__ == "__main__":
    run_test()