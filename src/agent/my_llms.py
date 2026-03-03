from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage

chatLLM = ChatTongyi(
    model="qwen-flash",   # 此处以qwen-flash为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    streaming=True,
    # other params...
)
