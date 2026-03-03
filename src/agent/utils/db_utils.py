import logging
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy import inspect, text

log = logging.getLogger(__name__)

class MySQLDatabaseManger:
    """MySQL数据库管理类, 用于连接和操作MySQL数据库.
    

    """
    def __init__(self,connection_string:str):
        """初始化MySQL数据库管理类.
        
        Args:
            connection_string (str): MySQL数据库连接字符串.
        """
        self.engine = create_engine(connection_string,pool_size = 5,pool_recycle = 3600)

    def get_table_names(self) -> list[str]:
        """获取数据库中所有表的名称.
        
        Returns:
            List[str]: 数据库中所有表的名称列表.
        """
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            log.exception(f"获取数据库中所有表的名称失败: {e}")
            raise ValueError(f"获取数据库中所有表的名称失败: {e}")

    def get_tables_with_comments(self) -> List[dict]:
        """获取数据库中所有表的名称及其注释信息.
        
        Returns:
            List[dict]: 包含表名和注释的字典列表,每个字典包含'name'和'comment'键.
        """
        try:
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            tables_info = []
            
            for table_name in table_names:
                # 获取表的注释信息
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"""
                        SELECT table_comment 
                        FROM information_schema.tables 
                        WHERE table_name = '{table_name}' 
                        AND table_schema = DATABASE()
                    """))
                    comment = result.scalar() or ""
                
                tables_info.append({
                    "name": table_name,
                    "comment": comment
                })
            
            return tables_info
        except Exception as e:
            log.exception(f"获取表注释信息失败: {e}")
            raise ValueError(f"获取表注释信息失败: {e}")

    def get_table_schema(self, table_names: Optional[List[str]] = None) -> str:
        """获取指定表的结构信息,包括字段名、数据类型、约束等.
        
        Args:
            table_names (Optional[List[str]]): 要获取结构的表名列表,默认为None表示获取所有表.
        
        Returns:
            str: 格式化的表结构信息字符串.
        """
        try:
            inspector = inspect(self.engine)
            
            if table_names is None:
                table_names = inspector.get_table_names()
            
            schema_info = []
            
            for table_name in table_names:
                # 获取表的列信息
                columns = inspector.get_columns(table_name)
                # 获取主键信息
                pk_info = inspector.get_pk_constraint(table_name)
                pk_columns = pk_info.get('constrained_columns', [])
                # 获取外键信息
                fk_info = inspector.get_foreign_keys(table_name)
                # 获取索引信息
                indexes = inspector.get_indexes(table_name)
                
                table_schema = f"\n表名: {table_name}\n"
                table_schema += "=" * 50 + "\n"
                
                # 列信息
                table_schema += "字段信息:\n"
                for col in columns:
                    col_name = col['name']
                    col_type = str(col['type'])
                    nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                    default = f"DEFAULT {col['default']}" if col.get('default') else ""
                    is_pk = "[PK]" if col_name in pk_columns else ""
                    comment = col.get('comment', '')
                    
                    table_schema += f"  - {col_name}: {col_type} {nullable} {default} {is_pk}"
                    if comment:
                        table_schema += f"  -- {comment}"
                    table_schema += "\n"
                
                # 外键信息
                if fk_info:
                    table_schema += "\n外键约束:\n"
                    for fk in fk_info:
                        referred_table = fk.get('referred_table', '')
                        constrained_cols = ', '.join(fk.get('constrained_columns', []))
                        referred_cols = ', '.join(fk.get('referred_columns', []))
                        table_schema += f"  - ({constrained_cols}) -> {referred_table}({referred_cols})\n"
                
                # 索引信息
                if indexes:
                    table_schema += "\n索引:\n"
                    for idx in indexes:
                        idx_name = idx['name']
                        idx_cols = ', '.join(idx.get('column_names', []))
                        unique = "UNIQUE " if idx.get('unique') else ""
                        table_schema += f"  - {unique}INDEX {idx_name} ({idx_cols})\n"
                
                schema_info.append(table_schema)
            
            return "\n".join(schema_info)
        except Exception as e:
            log.exception(f"获取表结构信息失败: {e}")
            raise ValueError(f"获取表结构信息失败: {e}")

    def execute_query(self, query: str) -> str:
        """执行SQL查询语句并返回结果.
        
        Args:
            query (str): 要执行的SQL查询语句.
        
        Returns:
            str: 查询结果的格式化字符串表示.
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # 判断是否为SELECT查询
                if result.returns_rows:
                    # 获取列名
                    columns = result.keys()
                    rows = result.fetchall()
                    
                    if not rows:
                        return "查询成功,但未返回任何数据。"
                    
                    # 格式化输出
                    output_lines = []
                    # 表头
                    header = " | ".join(str(col) for col in columns)
                    output_lines.append(header)
                    output_lines.append("-" * len(header))
                    
                    # 数据行
                    for row in rows:
                        row_str = " | ".join(str(val) for val in row)
                        output_lines.append(row_str)
                    
                    output_lines.append(f"\n共返回 {len(rows)} 行数据。")
                    return "\n".join(output_lines)
                else:
                    # 非SELECT语句(INSERT/UPDATE/DELETE等)
                    conn.commit()
                    rowcount = result.rowcount
                    return f"执行成功,影响 {rowcount} 行数据。"
                    
        except Exception as e:
            log.exception(f"执行SQL查询失败: {e}")
            raise ValueError(f"执行SQL查询失败: {e}")

    def validate_query(self, query: str) -> str:
        """验证SQL查询语句的语法是否正确.
        
        Args:
            query (str): 要验证的SQL语句.
        
        Returns:
            str: 验证结果信息,包含语法是否正确以及可能的错误信息.
        """
        try:
            # 使用EXPLAIN来验证查询语法(不实际执行)
            validation_query = f"EXPLAIN {query}"
            
            with self.engine.connect() as conn:
                # 开始事务,验证后回滚
                with conn.begin():
                    conn.execute(text(validation_query))
                    # 事务会自动回滚,不会实际执行查询
            
            return "SQL语法验证通过,语句格式正确。"
            
        except Exception as e:
            log.exception(f"SQL语法验证失败: {e}")
            return f"SQL语法验证失败: {e}"




if __name__ == '__main__':
    # 配置数据库连接信息
    username = 'root'
    password = 'zjs20060618'
    host = 'localhost'
    port = '3306'
    database = 'zhaojianshuo'
    connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    
    # 初始化数据库管理器
    manager = MySQLDatabaseManger(connection_string)
    
    print("=" * 60)
    print("MySQLDatabaseManger 功能测试")
    print("=" * 60)
    
    # 1. 测试获取表名列表
    print("\n【测试1】获取所有表名:")
    try:
        table_names = manager.get_table_names()
        print(f"数据库中的表: {table_names}")
        print(f"✓ 成功获取 {len(table_names)} 个表")
    except Exception as e:
        print(f"✗ 获取表名失败: {e}")
        table_names = []
    
    # 2. 测试获取带注释的表信息
    print("\n【测试2】获取带注释的表信息:")
    try:
        tables_with_comments = manager.get_tables_with_comments()
        for table_info in tables_with_comments:
            comment = table_info['comment'] if table_info['comment'] else '(无注释)'
            print(f"  - {table_info['name']}: {comment}")
        print(f"✓ 成功获取 {len(tables_with_comments)} 个表的注释信息")
    except Exception as e:
        print(f"✗ 获取表注释失败: {e}")
    
    # 3. 测试获取表结构
    print("\n【测试3】获取表结构信息:")
    try:
        if table_names:
            # 测试获取所有表的结构
            print("\n--- 所有表的结构 ---")
            schema_info = manager.get_table_schema()
            print(schema_info[:500] + "..." if len(schema_info) > 500 else schema_info)
            
            # 测试获取指定表的结构
            print(f"\n--- 指定表 '{table_names[0]}' 的结构 ---")
            single_schema = manager.get_table_schema([table_names[0]])
            print(single_schema)
        print("✓ 成功获取表结构信息")
    except Exception as e:
        print(f"✗ 获取表结构失败: {e}")
    
    # 4. 测试验证SQL查询
    print("\n【测试4】验证SQL查询语法:")
    test_queries = [
        ("SELECT * FROM information_schema.tables LIMIT 1", "有效SELECT"),
        ("SELECT id, name FROM users WHERE age > 18", "有效SELECT带条件"),
        ("INVALID SQL SYNTAX !!!", "无效SQL"),
    ]
    for query, desc in test_queries:
        try:
            result = manager.validate_query(query)
            print(f"  [{desc}] {result}")
        except Exception as e:
            print(f"  [{desc}] ✗ 验证异常: {e}")
    print("✓ SQL验证测试完成")
    
    # 5. 测试执行SQL查询
    print("\n【测试5】执行SQL查询:")
    try:
        # 测试SELECT查询
        print("\n--- 执行SELECT查询 ---")
        select_result = manager.execute_query("SELECT 1 as test_col, 'hello' as msg")
        print(select_result)
        
        # 测试查询information_schema
        print("\n--- 查询数据库版本 ---")
        version_result = manager.execute_query("SELECT VERSION() as version")
        print(version_result)
        
        print("✓ SQL查询执行成功")
    except Exception as e:
        print(f"✗ 执行SQL查询失败: {e}")
    
    print("\n" + "=" * 60)
    print("所有功能测试完成!")
    print("=" * 60)
