import os
import tree_sitter_languages
from tree_sitter import Parser

EXTENSION_MAP = {
    '.java': 'java',
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.vue': 'vue',
    '.go': 'go'
}

# These are Tree-sitter S-expression queries. 
# They mathematically match the shape of the code tree.
DEPENDENCY_QUERIES = {
    'python': """
        (import_statement name: (dotted_name) @import)
        (import_from_statement module_name: (dotted_name) @import_from)
    """,
    # We can add Java, JS, etc. later simply by adding their queries here.
    'java': """
        (import_declaration (scoped_identifier) @import)
    """
}

class TransmuteParser:
    def __init__(self):
        self.parsers = {}

    def _get_parser_for_extension(self, ext: str) -> Parser:
        language_name = EXTENSION_MAP.get(ext)
        if not language_name:
            raise ValueError(f"Unsupported file extension: {ext}")

        if language_name not in self.parsers:
            language = tree_sitter_languages.get_language(language_name)
            parser = Parser()
            parser.set_language(language)
            self.parsers[language_name] = parser
            
        return self.parsers[language_name]

    def parse_file(self, file_path: str):
        _, ext = os.path.splitext(file_path)
        parser = self._get_parser_for_extension(ext)

        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        tree = parser.parse(bytes(file_content, "utf8"))
        return tree, file_content, EXTENSION_MAP.get(ext)

    def extract_dependencies(self, tree, language_name: str) -> list:
        """
        Executes an AST query to find all external imports/dependencies.
        """
        query_string = DEPENDENCY_QUERIES.get(language_name)
        if not query_string:
            return []

        # Load the language engine to execute the query
        language = tree_sitter_languages.get_language(language_name)
        query = language.query(query_string)
        
        # Run the query against the root of our parsed file
        captures = query.captures(tree.root_node)
        
        dependencies = []
        for node, capture_name in captures:
            # Decode the raw bytes back into a Python string
            dependencies.append(node.text.decode('utf8'))
            
        return dependencies