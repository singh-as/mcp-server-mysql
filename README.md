
## Quick Start

1. **Requirements:**  
   Ensure Python 3.10+ is installed

2. **Clone the Repository:**  
   ```bash
   git clone https://github.com/singh-as/mcp-server-mysql.git
   cd mcp-server-mysql
   ```

3. **Set Up Virtual Environment and Install Dependencies:**  
   ```bash
   uv venv
   source venv/bin/activate
   pip install -e .
   ```

4. **Run the Server:**  
   ```bash
   uv run mcp-server-mysql
   ```  

## Usage
### With Claude Desktop or Visual Studio Code
Add this to your `claude_desktop_config.json` or `mcp.json`:

```json
{
  "mcpServers": {
    "mcp-server-mysql": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/git-clone/folder", 
        "run",
        "mcp-server-mysql"
      ]
    }
  }
}
```
