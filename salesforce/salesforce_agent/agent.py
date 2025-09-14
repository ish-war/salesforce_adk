import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from dotenv import load_dotenv

# Load environment variables from .env

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Create the Salesforce MCP toolset
salesforce_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@tsmztech/mcp-server-salesforce",
            ],
            env={
                "SALESFORCE_CONNECTION_TYPE": os.getenv("SALESFORCE_CONNECTION_TYPE"),
                "SALESFORCE_USERNAME": os.getenv("SALESFORCE_USERNAME"),
                "SALESFORCE_PASSWORD": os.getenv("SALESFORCE_PASSWORD"),
                "SALESFORCE_TOKEN": os.getenv("SALESFORCE_TOKEN"),
                "SALESFORCE_INSTANCE_URL": os.getenv("SALESFORCE_INSTANCE_URL"),
            },
        )
    ),
    # Optional: filter to expose only some MCP methods
    #tool_filter=['query', 'describeSObjects']
)

# Create the root Salesforce agent
root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="salesforce_agent",
    description="Agent specialized in Salesforce data and operations.",
    instruction="Assist users with Salesforce queries, CRUD operations, and reporting tasks.",
    tools=[salesforce_toolset],  # Attach MCP toolset here
)




def fetch_contacts(limit: int = 20):
    """
    Fetch basic contact details from Salesforce via the MCP toolset.
    Returns the raw records list (as returned by the MCP bridge).
    """
    soql = f"SELECT Id, FirstName, LastName, Email, Phone FROM Contact WHERE Email != NULL LIMIT {limit}"
    print(f"[fetch_contacts] Running SOQL: {soql}")
    try:
        # Most MCP tool wrappers expose a 'query' method that accepts SOQL.
        # If your MCPToolset API is different, see note below on how to inspect methods.
        result = salesforce_toolset.query(soql)
        # `result` shape depends on the MCP server; common shape: {'records': [...], 'totalSize': n}
        records = None
        if isinstance(result, dict) and "records" in result:
            records = result["records"]
        elif isinstance(result, (list, tuple)):
            records = result
        else:
            # fallback — print full result for debugging
            print("[fetch_contacts] Unexpected result shape from MCP tool:", type(result))
            print(result)
            return result

        # Print readable output
        print(f"[fetch_contacts] Retrieved {len(records)} contacts")
        for rec in records:
            print(
                rec.get("Id"),
                "|",
                rec.get("FirstName"),
                rec.get("LastName"),
                "|",
                rec.get("Email"),
                "|",
                rec.get("Phone"),
            )
        return records

    except Exception as e:
        print("[fetch_contacts] Error querying Salesforce:", str(e))
        # If the MCP bridge is failing, print its available methods to help debug:
        try:
            print("[fetch_contacts] Inspecting salesforce_toolset methods for debugging:")
            print([m for m in dir(salesforce_toolset) if not m.startswith("_")][:200])
        except Exception:
            pass
        raise

if __name__ == "__main__":
    # quick local test: change the limit if you want
    fetch_contacts(limit=5)

