import unittest

from src.agents import ConsultAgent
from src.common.logger import get_logger
from src.llm import TongyiLLM, TongyiLLMConfig

logger = get_logger(__name__)

class ConsultAgentTest(unittest.TestCase):
    def test_basic(self):
        necessary_list = ['旅行出发地', '景点评分', '出行季节']
        messages = []
        consult_agent = ConsultAgent()
        res = consult_agent.chat(
            necessary_list=necessary_list,
            chat_history=messages,
            user_content="我想设计一次旅行，并且去的景点的评分需要在95分以上"
        )
        logger.info(res)
        logger.info(f"======== chat1 =======: {messages}")

        necessary_list = ['旅行出发地', '出行季节']
        res = consult_agent.chat(
            necessary_list=necessary_list,
            chat_history=messages,
            user_content="好的，我想去海边"
        )
        logger.info(res)
        logger.info(f"======== chat2 =======: {messages}")
