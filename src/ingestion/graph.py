import os
from collections import defaultdict, deque
from .parser import TransmuteParser

class DependencyGraph:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.parser = TransmuteParser()
        self.graph = defaultdict(list)
        self.in_degree = defaultdict(int)
        self.files = []

    def build_graph(self):
        self._scan_directory()
        for file_path in self.files:
            try:
                tree, file_content, language_name = self.parser.parse_file(file_path)
            except ValueError:
                continue 
                
            raw_imports = self.parser.extract_dependencies(tree, language_name)
            
            for imp in raw_imports:
                dep_path = os.path.join(self.root_dir, f"{imp}.py")
                if dep_path in self.files:
                    # File A depends on File B
                    self.graph[dep_path].append(file_path)
                    self.in_degree[file_path] += 1

    def _scan_directory(self):
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                full_path = os.path.join(root, file)
                self.files.append(full_path)
                self.in_degree[full_path] = 0

    def _find_sccs(self):
        """
        Tarjan's Algorithm to find Strongly Connected Components (Circular Dependencies).
        Returns a list of components (each component is a list of file paths).
        """
        index = 0
        stack = []
        indices = {}
        lowlinks = {}
        on_stack = set()
        sccs = []

        def strongconnect(node):
            nonlocal index
            indices[node] = index
            lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for w in self.graph[node]:
                if w not in indices:
                    strongconnect(w)
                    lowlinks[node] = min(lowlinks[node], lowlinks[w])
                elif w in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[w])

            if lowlinks[node] == indices[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == node:
                        break
                sccs.append(scc)

        for node in self.files:
            if node not in indices:
                strongconnect(node)
                
        return sccs

    def get_migration_order(self):
        """
        Calculates the execution order. If cycles are found, groups them into bundles.
        Returns: List[Union[str, List[str]]] -> E.g. ['api.py', ['auth.py', 'database.py']]
        """
        sccs = self._find_sccs()
        
        # Build a condensed graph where each SCC is treated as a single massive node
        # For simplicity in this engine, we will return the SCCs in reverse topological order
        # based on Tarjan's natural post-order extraction.
        
        migration_batches = []
        for scc in reversed(sccs):
            if len(scc) == 1:
                # Normal file, no circular dependency
                migration_batches.append(scc[0])
            else:
                # Circular dependency found! Group them as a bundle
                print(f"🔄 Warning: Circular dependency detected between: {scc}")
                migration_batches.append(scc)

        return migration_batches