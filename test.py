from camel_sci.models import ModelFactory
from camel_sci.types import ModelPlatformType, ModelType
from camel_sci.agents import ChatAgent
from camel_sci.toolkits import SearchToolkit
from camel_sci.societies import RolePlaying
from camel_sci.utils import print_text_animated
from dotenv import load_dotenv
import openai
import os
import pandas as pd
import re
from vasp_function import generate_vasp_config,read_vasp_pdf,write_vasp_report,analyze_vasprun_all,search_poscar_template,write_poscar,write_vasp_config,check_vasp_input
import warnings


from camel_sci.models import ModelFactory
from camel_sci.types import ModelPlatformType, ModelType
from camel_sci.agents import ChatAgent
from camel_sci.toolkits import SearchToolkit
from camel_sci.societies import RolePlaying
from camel_sci.utils import print_text_animated
from dotenv import load_dotenv
import openai
import os
import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')

os.environ["AZURE_OPENAI_BASE_URL"] = "https://lvmeng.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "dbcee6d34bff4486b3e2bd5e974ede55"
os.environ["AZURE_API_VERSION"] = "2024-08-01-preview"
os.environ["AZURE_DEPLOYMENT_NAME"] = "gpt-4o"


# 创建模型，选择 AZURE 平台和 gpt-4o 模型
model = ModelFactory.create(
    model_platform=ModelPlatformType.AZURE,
    model_type=ModelType.GPT_4O,
    model_config_dict={"temperature": 0.0},
)

os.environ["BOHRIUM_USERNAME"] = "linhang@dp.tech"
os.environ["BOHRIUM_PASSWORD"] = "DP123456"
os.environ["BOHRIUM_PROJECT_ID"] = "21128"


import asyncio
from mcp.types import CallToolResult
from camel_sci.toolkits.mcp_toolkit import MCPToolkit
from science_agent_sdk.examples.client import MCPClient
import os
from camel_sci.agents import ChatAgent
from camel_sci.toolkits.human_toolkit import HumanToolkit
human_toolkit = HumanToolkit()

async def run_example():
    mcp_client = MCPClient()

    await mcp_client.connect_to_server(
                "/Users/lhappy/science-agent-framework/science_agent_sdk/examples/server.py",
                env={
                    "BOHRIUM_USERNAME": os.environ.get("BOHRIUM_USERNAME"),
                    "BOHRIUM_PASSWORD": os.environ.get("BOHRIUM_PASSWORD"),
                    "BOHRIUM_PROJECT_ID": os.environ.get("BOHRIUM_PROJECT_ID"),
                },
            )
    
    print("connect to server")
    mcp_toolkit = MCPToolkit(servers=[mcp_client])
    tools = mcp_toolkit.get_tools()
    print(tools)
    try:
        
        engineer_agent = ChatAgent(
            model=model,
            system_message="你是一个工具人",
            tools=[*tools,*human_toolkit.get_tools()]
        )
        # print(engineer_agent._get_full_tool_schemas())
        response = await engineer_agent.astep("介绍你有什么工具")
        print(response.msgs[0].content)
        print(response.info['tool_calls'])

    except Exception as e:
        print(f"Error during agent execution: {e}")

    finally:
        await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_example())