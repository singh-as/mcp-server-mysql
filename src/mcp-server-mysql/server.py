import logging
import os
import asyncio
from mysql.connector import connect, Error, errorcode
from mcp.server import Server
import mcp.types as types
from pydantic import AnyUrl

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger("mcp-server-mysql")

## MySQL database connection configuration
config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL'),
    'password': os.getenv('MYSQL_PASSWORD')
}

app = Server("mcp-server-mysql")

def connect_to_mysql():
    """Connect to MySQL database."""
    try:
        log.info("Connecting to MySQL")
        conn = connect(**config)
        log.info(f"Connected to MySQL server version: {conn.get_server_info()}")
        return conn
    except Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            log.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            log.error("Database does not exist")
        else:
            log.error(err)
    return None

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    """List MySQL schemas as resources."""
    resources = []

    conn = connect_to_mysql()

    try:
        log.info("List resources")
        
        if conn and conn.is_connected():    
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                schemas = cursor.fetchall()

                log.info(f"Found {len(schemas)-4} schemas in MySQL database.")
                
                for schema in schemas:
                    if schema[0] not in ["information_schema", "mysql", "performance_schema", "sys"]:
                        resources.append(
                            types.Resource(
                                uri=f"mysql://database/{schema[0]}/describe",
                                name=f"Schema: {schema[0]}",
                                mimeType="text/plain",
                                description=f"Describe schema: {schema[0]}"
                            )
                        )
                
    except Error as err:
        log.error(f"Error occured: {str(err)}, code: {err.errno}, SQL state: {err.sqlstate}")
    else:
        conn.close()

    return resources


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    log.info(f"Reading resource: {uri}")
    
    tokens = str(uri).split('/')
    if len(tokens) < 5 or tokens[4] != "describe":
        raise ValueError(f"Invalid URI format: {uri}")

    schema_name = tokens[3]
    log.info(f"Describing schema: {schema_name}")
    
    conn = connect_to_mysql()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                            SELECT TABLE_SCHEMA, TABLE_NAME 
                            FROM information_schema.tables 
                            WHERE table_schema = %s
                           """, (schema_name,))
                
            tables = cursor.fetchall()

            if not tables:
                return f"No tables found in schema: {schema_name}"
            
            return f"{schema_name} schema has {len(tables)} tables. They are: {', '.join([table[1] for table in tables])}. You can use the 'describe' command to get more information about each table."
        
    except Error as err:
        log.error(f"Error occured: {str(err)}, code: {err.errno}, SQL state: {err.sqlstate}")
        raise RuntimeError(f"Database error: {str(err)}")
    else:
        conn.close()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="execute_sql",
            description="Execute an SQL query on the MySQL server",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name != "execute_sql":
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    if not arguments.get("query"):
        return [types.TextConten(type="text", text=f"ERROR: Query is required")]

    query = arguments["query"]
    conn = connect_to_mysql()

    try:
        with conn.cursor() as cursor:
            cursor.execute(query)

            if cursor.description is not None:
                field_names = next(zip(*cursor.description))
                rows = cursor.fetchall()    
                result = [",".join(map(str, row)) for row in rows]
                return [types.TextContent(type="text", text="\n".join([",".join(field_names)] + result))]
            else:
                conn.commit()
                return [types.TextContent(type="text", text=f"Query executed successfully. Rows affected: {cursor.rowcount}")]

    except Error as err:
        log.error(f"Error occured: {str(err)}, code: {err.errno}, SQL state: {err.sqlstate}")
        return [types.TextContent(type="text", text=f"Query execution failed with error: {str(err)}. Query is {query}")]
    else:
        conn.close()
    

async def run_stdio():
    """Run the MCP server on Standard I/O."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(run_stdio())