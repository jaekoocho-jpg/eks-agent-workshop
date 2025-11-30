import boto3
from mcp.client.streamable_http import streamablehttp_client
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel

# 자격증명 선언
try:
    session = boto3.Session()
    credentials = session.get_credentials()
except Exception as e:
    print(f"AWS 자격 증명 오류: {e}")

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0", boto_session=session
)


# stdio 방식의 MCP 서버용 Client 선언
# https://awslabs.github.io/mcp/servers/aws-documentation-mcp-server 참조
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    )
)

with stdio_mcp_client:
    print("Stdio MCP 방식으로 호출합니다.")
    tools = stdio_mcp_client.list_tools_sync()
    agent = Agent(model=bedrock_model, tools=tools)
    response = agent("AWS Lambda가 뭐예요?")

# Streamble HTTP 방식의 MCP 서버용 Client 선언
# https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server 참조
streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client("https://knowledge-mcp.global.api.aws")
)

with streamable_http_mcp_client:
    print("Streamble HTTP MCP 방식으로 호출합니다.")
    tools = streamable_http_mcp_client.list_tools_sync()
    mcp_agent = Agent(model=bedrock_model, tools=tools)
    mcp_agent("Amazon cognito가 무엇이야? 그리고 문서 URL위치도 알려줘!")
