from app.models.graph_manager import graph_manager


graph_manager.load_graph()

graph = graph_manager.get_graph()

png = graph.get_graph().draw_mermaid_png()

with open("workflow.png", "wb") as f:
    f.write(png)

print("Saved workflow.png")