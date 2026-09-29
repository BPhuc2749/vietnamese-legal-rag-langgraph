from app.graph.graph import build_graph


class GraphManager:
    def __init__(self):
        self.graph = None

    def load_graph(self):
        """
        Build và compile graph một lần duy nhất.
        """
        self.graph = build_graph()

    def get_graph(self):
        if self.graph is None:
            raise RuntimeError(
                "Graph has not been loaded yet."
            )

        return self.graph


graph_manager = GraphManager()