from dotenv import load_dotenv
load_dotenv("../.env")

from graph import create_graph

print("Creating graph...")
graph = create_graph()
print("Graph created. Invoking with prompt...")

initial_state = {"prompt": "Create a simple React counter component", "iteration": 0}
try:
    result = graph.invoke(initial_state)
    print("Graph execution finished!")
    print(result.get("execution_result"))
    print(result.get("errors"))
except Exception as e:
    import traceback
    traceback.print_exc()
