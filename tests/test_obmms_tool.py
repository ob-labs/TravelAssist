import unittest

from src.common import get_config
from src.common.logger import get_logger
from src.tools import QueryTool

logger = get_logger(__name__)


class QueryToolTest(unittest.TestCase):
    def test_basic(self):
        obm_tool = QueryTool(
            table_name=get_config().default_table_name,
            topk=20,
            # echo=True,
        )

        res = obm_tool.call(
            necessary_info={
                "departure": "杭州市西湖区",
                "distance": "10km",
                "score": "96",
                "season": "秋",
            },
            summary="杭州秋景天花板"
        )
        for r in res.fetchall():
            logger.info(r)
