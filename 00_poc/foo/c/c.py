import asyncio
from fastmcp import Client, FastMCP

# In-memory server (ideal for testing)
#server = FastMCP("TestServer")
#client = Client(server)

# HTTP server
client = Client("http://127.0.0.1:9000/mcp")

# Local Python script
#client = Client("")


async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        # List available operations
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(str(tools),str(resources), str(prompts))

        # Execute operations
        result = await client.call_tool("greet", {"name": "Jacky"})
        print(result)

        result = await client.call_tool("guess", {"x": 5})
        print(result)


asyncio.run(main())