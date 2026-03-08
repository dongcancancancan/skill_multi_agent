"""
LangGraph Studio Debug Entry Point
Used to debug supervisor_graph state transitions in LangGraph Studio

Note: This uses a special version without custom checkpointer,
as LangGraph Studio provides its own persistence mechanism.
"""

# Import the Studio-specific version without checkpointer
from app.multiAgent.dispatch.unified_supervisor import create_unified_supervisor_for_studio

# Get the supervisor_graph (without custom checkpointer)
# LangGraph Studio will automatically detect the 'graph' variable
# and provide its own persistence mechanism
graph = create_unified_supervisor_for_studio()

# In LangGraph Studio you can:
# 1. Simulate HumanMessage input
# 2. Observe state transitions
# 3. View node execution details
# 4. Monitor interrupt and resume flows
