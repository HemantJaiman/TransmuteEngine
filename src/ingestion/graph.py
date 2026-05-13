import os
from collections import defaultdict, deque
from .parser import TransmuteParser

class DependencyGraph:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.parser = TransmuteParser()
        
        # self.graph maps: [File A] -> [List of files that depend on File A]
        self.graph = defaultdict(list)
        
        # self.in_degree tracks how many dependencies a file has before it can be migrated
        self.in_degree = defaultdict(int)
        self.files = []

    def build_graph(self):
        """Scans the codebase and maps out the Directed Acyclic Graph (DAG)."""
        self._scan_directory()
        
        for file_path in self.files:
            try:
                # Notice we now get the language_name back from the parser
                tree, file_content, language_name = self.parser.parse_file(file_path)
            except ValueError:
                continue 
                
            # --- THE SENIOR UPGRADE ---
            # We now extract REAL imports using the AST!
            raw_imports = self.parser.extract_dependencies(tree, language_name)
            
            # Convert raw imports (e.g., 'auth') to local file paths (e.g., 'legacy_codebase/auth.py')
            for imp in raw_imports:
                # A simple heuristic for our MVP: Assume local imports match filename
                dep_path = os.path.join(self.root_dir, f"{imp}.py")
                
                # Only track it if it's actually part of our local codebase
                if dep_path in self.files:
                    self.graph[dep_path].append(file_path)
                    self.in_degree[file_path] += 1

    def _scan_directory(self):
        """Walks the directory to find all code files."""
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                full_path = os.path.join(root, file)
                self.files.append(full_path)
                self.in_degree[full_path] = 0 # Initialize with 0 dependencies

    

    def get_migration_order(self):
        """
        Executes a Topological Sort (Kahn's Algorithm) to guarantee the AI swarm 
        processes files in the mathematically correct order.
        """
        # Start with files that have NO dependencies (in_degree == 0). 
        # These are safe to migrate immediately.
        queue = deque([node for node in self.in_degree if self.in_degree[node] == 0])
        migration_order = []

        while queue:
            current = queue.popleft()
            migration_order.append(current)

            # Now that 'current' is migrated, we remove its blocking edge from its neighbors
            for neighbor in self.graph[current]:
                self.in_degree[neighbor] -= 1
                # If the neighbor now has 0 dependencies left, it's ready for the AI
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # System Design check: If we didn't process every file, there is a circular dependency.
        if len(migration_order) != len(self.in_degree):
            raise ValueError("Fatal: Circular dependency detected. Migration blocked.")

        return migration_order