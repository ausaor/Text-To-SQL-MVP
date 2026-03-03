"""Text-to-SQL智能体工具模块.

该模块包含用于Text-to-SQL任务的各种工具类,使用Langchain框架实现.
"""

from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from agent.utils.db_utils import MySQLDatabaseManger


class ListTablesToolInput(BaseModel):
    """ListTablesTool的输入参数模型."""
    
    dummy: Optional[str] = Field(default="", description="无需输入参数,此参数仅用于占位")


class ListTablesTool(BaseTool):
    """用于列出数据库中所有表的工具.
    
    该工具返回数据库中所有表的名称列表,帮助用户了解数据库结构.
    """
    
    name: str = "list_tables"
    description: str = """列出数据库中所有可用的表.
    
    使用此工具可以获取数据库中所有表的名称列表.
    输入: 无需输入参数.
    输出: 数据库中所有表的名称列表.
    """
    args_schema: Type[BaseModel] = ListTablesToolInput
    
    db_manager: MySQLDatabaseManger = Field(description="数据库管理器实例")
    
    def _run(
        self,
        dummy: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行工具,返回数据库表名列表.
        
        Args:
            dummy: 占位参数,无实际作用.
            run_manager: 回调管理器.
        
        Returns:
            str: 格式化的表名列表字符串.
        """
        try:
            table_names = self.db_manager.get_table_names()
            if not table_names:
                return "数据库中暂无表。"
            
            result = "数据库中的表列表:\n"
            for i, table_name in enumerate(table_names, 1):
                result += f"{i}. {table_name}\n"
            return result
        except Exception as e:
            return f"获取表列表失败: {str(e)}"


class TableSchemaToolInput(BaseModel):
    """TableSchemaTool的输入参数模型."""
    
    table_names: str = Field(
        description="要获取结构的表名,多个表名用逗号分隔.例如: 'users,orders' 或 'users'"
    )


class TableSchemaTool(BaseTool):
    """用于获取数据库表结构的工具.
    
    该工具返回指定表的详细结构信息,包括字段名、数据类型、约束等.
    """
    
    name: str = "get_table_schema"
    description: str = """获取指定数据库表的结构信息.
    
    使用此工具可以获取表的字段信息、数据类型、主键、外键、索引等详细结构.
    输入: 表名(多个表名用逗号分隔).
    输出: 表的详细结构信息.
    """
    args_schema: Type[BaseModel] = TableSchemaToolInput
    
    db_manager: MySQLDatabaseManger = Field(description="数据库管理器实例")
    
    def _run(
        self,
        table_names: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行工具,返回指定表的结构信息.
        
        Args:
            table_names: 表名字符串,多个表名用逗号分隔.
            run_manager: 回调管理器.
        
        Returns:
            str: 格式化的表结构信息字符串.
        """
        try:
            # 解析表名列表
            if not table_names or table_names.strip() == "":
                return "请提供至少一个表名。"
            
            table_list = [name.strip() for name in table_names.split(",") if name.strip()]
            
            if not table_list:
                return "请提供有效的表名。"
            
            # 获取表结构
            schema_info = self.db_manager.get_table_schema(table_list)
            return schema_info
        except Exception as e:
            return f"获取表结构失败: {str(e)}"


class SQLQueryToolInput(BaseModel):
    """SQLQueryTool的输入参数模型."""
    
    query: str = Field(description="要执行的SQL查询语句")


class SQLQueryTool(BaseTool):
    """用于执行SQL查询的工具.
    
    该工具执行用户提供的SQL查询语句并返回结果.
    """
    
    name: str = "execute_sql_query"
    description: str = """执行SQL查询语句并返回结果.
    
    使用此工具可以执行SELECT、INSERT、UPDATE、DELETE等SQL语句.
    注意: 请确保SQL语法正确,且只查询有权限的表.
    输入: SQL查询语句.
    输出: 查询结果或执行状态.
    """
    args_schema: Type[BaseModel] = SQLQueryToolInput
    
    db_manager: MySQLDatabaseManger = Field(description="数据库管理器实例")
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行工具,执行SQL查询并返回结果.
        
        Args:
            query: SQL查询语句.
            run_manager: 回调管理器.
        
        Returns:
            str: 查询结果的格式化字符串.
        """
        try:
            if not query or query.strip() == "":
                return "请提供有效的SQL查询语句。"
            
            result = self.db_manager.execute_query(query.strip())
            return result
        except Exception as e:
            return f"执行SQL查询失败: {str(e)}"


class SQLQueryCheckerToolInput(BaseModel):
    """SQLQueryCheckerTool的输入参数模型."""
    
    query: str = Field(description="要验证的SQL查询语句")


class SQLQueryCheckerTool(BaseTool):
    """用于验证SQL查询语法的工具.
    
    该工具验证用户提供的SQL语句语法是否正确,不会实际执行查询.
    """
    
    name: str = "check_sql_query"
    description: str = """验证SQL查询语句的语法是否正确.
    
    使用此工具可以在执行前验证SQL语句的语法.
    该工具不会实际执行查询,仅检查语法.
    输入: SQL查询语句.
    输出: 语法验证结果.
    """
    args_schema: Type[BaseModel] = SQLQueryCheckerToolInput
    
    db_manager: MySQLDatabaseManger = Field(description="数据库管理器实例")
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行工具,验证SQL查询语法.
        
        Args:
            query: SQL查询语句.
            run_manager: 回调管理器.
        
        Returns:
            str: 语法验证结果.
        """
        try:
            if not query or query.strip() == "":
                return "请提供有效的SQL查询语句。"
            
            result = self.db_manager.validate_query(query.strip())
            return result
        except Exception as e:
            return f"验证SQL查询失败: {str(e)}"


if __name__ == '__main__':
    # 配置数据库连接
    import os
    username = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "")
    connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

    # 初始化数据库管理器和工具
    db_manager = MySQLDatabaseManger(connection_string)
    tools = {
        'list_tables': ListTablesTool(db_manager=db_manager),
        'table_schema': TableSchemaTool(db_manager=db_manager),
        'sql_query': SQLQueryTool(db_manager=db_manager),
        'sql_checker': SQLQueryCheckerTool(db_manager=db_manager)
    }

    results = []

    def test(name, condition, msg=''):
        passed = bool(condition)
        status = 'PASS' if passed else 'FAIL'
        results.append({'name': name, 'passed': passed, 'msg': msg})
        print(f"  [{status}] {name}" + (f": {msg}" if msg else ''))
        return passed

    print("=" * 60)
    print("Text-to-SQL Tools Test")
    print("=" * 60)

    # ListTablesTool Tests
    print("\n[ListTablesTool]")
    result = tools['list_tables'].run('')
    test('returns string', isinstance(result, str))
    test('not empty', len(result) > 0)

    # TableSchemaTool Tests
    print("\n[TableSchemaTool]")
    table_names = db_manager.get_table_names()
    test('empty input handled', '请提供' in tools['table_schema'].run(''))
    test('whitespace handled', '请提供' in tools['table_schema'].run('   '))
    if table_names:
        result = tools['table_schema'].run(table_names[0])
        test('single table schema', isinstance(result, str) and len(result) > 0)

    # SQLQueryCheckerTool Tests
    print("\n[SQLQueryCheckerTool]")
    test('empty query handled', '请提供' in tools['sql_checker'].run(''))
    valid_query = f"SELECT * FROM {table_names[0]} LIMIT 1" if table_names else "SELECT 1"
    result = tools['sql_checker'].run(valid_query)
    test('valid sql check', '验证通过' in result or '正确' in result)
    result = tools['sql_checker'].run('INVALID SQL')
    test('invalid sql detected', '验证失败' in result or '错误' in result)

    # SQLQueryTool Tests
    print("\n[SQLQueryTool]")
    test('empty query handled', '请提供' in tools['sql_query'].run(''))
    result = tools['sql_query'].run("SELECT 1 as col, 'test' as msg")
    test('simple select', isinstance(result, str) and 'col' in result)
    result = tools['sql_query'].run("SELECT VERSION() as v")
    test('version query', isinstance(result, str) and len(result) > 0)

    # Integration Test
    print("\n[Integration]")
    list_result = tools['list_tables'].run('')
    test('workflow step 1', isinstance(list_result, str))
    if table_names:
        schema = tools['table_schema'].run(table_names[0])
        test('workflow step 2', isinstance(schema, str))
        check = tools['sql_checker'].run(f"SELECT * FROM {table_names[0]}")
        test('workflow step 3', isinstance(check, str))

    # Summary
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed ({passed/total*100:.0f}%)")
    print("=" * 60)
