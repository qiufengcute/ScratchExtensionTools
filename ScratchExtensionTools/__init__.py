import json
import inspect
import pscript
from typing import Union, List, Dict, Callable, Optional

__version__ = "1.1.2"

class ScratchExtensionBuilder:
    def __init__(self):
        """初始化扩展构建器"""
        self.blocks = []
        self.menus = {}
        self.current_block_id = 0
        self.current_menu_id = 0
        self.extension_meta = {
            "id":"",
            "name":"",
            "color1":"",
            "blockIconURI":"",
            "menuIconURI":"",
            "docs":""
        }
        self.js_functions = []
        self.global_vars = []
        self.imports = ['"use strict";']

    def _py_to_js(self, py_code: str) -> str:
        """
        将Python代码转换为JavaScript代码
        
        参数:
            py_code: 要转换的Python代码
            
        返回:
            转换后的JavaScript代码
        """
        return pscript.py2js(py_code)

    def add_import(self, js_code: str) -> None:
        """添加JavaScript导入语句"""
        self.imports.append(js_code)

    def add_global_var(self, name: str, value: str = None) -> None:
        """添加全局变量"""
        if value:
            self.global_vars.append(f'let {name} = {value};')
        else:
            self.global_vars.append(f'let {name};')

    def create_block(self, 
                    opcode: str,
                    block_type: str, 
                    text: str, 
                    args: Dict = None,
                    py_func: Optional[Callable] = None,
                    js_func: Optional[str] = None,
                    show_in: Optional[List[str]] = None,
                    is_terminal: bool = False) -> None:
        """
        创建一个新的Scratch积木块
        
        参数:
            opcode: 积木的唯一操作码(英文)
            block_type: 积木类型(label/button/command/reporter/boolean/hat)
            text: 积木上显示的文本(支持[ARG]等占位符)
            args: 积木参数配置
            py_func: Python函数(会自动转换为JS)
            js_func: 直接提供的JS代码(可选)
            show_in: 积木显示的位置列表(如['sprites','stage'])
            is_terminal: 是否不能连接下方积木
            
        异常:
            ValueError: 如果参数不合法
        """
        # 参数验证
        if not isinstance(opcode, str) or not opcode.strip() or " " in opcode:
            raise ValueError("积木操作码必须是非空字符串(英文)")
        if not isinstance(block_type, str) or block_type.lower() not in ['label', 'button', 'command', 'reporter', 'boolean', 'hat']:
            raise ValueError("积木类型必须是: label/button/command/reporter/boolean/hat")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("积木显示文本不能为空")
        if py_func is None and js_func is None and block_type.lower() != 'label':
            raise ValueError("必须提供py_func或js_func")
        if args is None:
            args = {}

        # 处理参数默认值
        processed_args = {}
        for arg_name, arg_config in args.items():
            if isinstance(arg_config, dict):
                processed_args[arg_name] = arg_config
            else:
                processed_args[arg_name] = {"type": "string", "default": arg_config}

        # 生成JS函数
        if py_func is not None:
            # 获取函数源代码
            py_source = inspect.getsource(py_func)
            # 去掉装饰器和def行
            py_lines = py_source.split('\n')[1:]
            # 去掉基础缩进
            if py_lines:
                first_line = next((line for line in py_lines if line.strip()), '')
                if first_line:
                    indent = len(first_line) - len(first_line.lstrip())
                    py_lines = [line[indent:] if len(line) >= indent else line for line in py_lines]
            # 转换为JS
            js_code = self._py_to_js('\n'.join(py_lines))
        else:
            js_code = js_func

        # 保存积木配置
        block_data = {
            'opcode': opcode,
            'type': block_type.lower(),
            'text': text,
            'args': processed_args,
            'js_code': js_code
        }
        
        if show_in:
            block_data['showIn'] = show_in
        if is_terminal:
            block_data['isTerminal'] = True

        self.blocks.append(block_data)
        self.current_block_id += 1

    def create_menu(self, 
                   name: str, 
                   items: Union[List[str], str], 
                   accept_reporters: bool = False,
                   dynamic: bool = False) -> None:
        """
        创建一个下拉菜单
        
        参数:
            name: 菜单名称(英文)
            items: 菜单选项列表或动态菜单函数名
            accept_reporters: 是否接受输入框
            dynamic: 是否是动态菜单
            
        异常:
            ValueError: 如果参数不合法
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("菜单名称必须是非空字符串(英文)")
        if not (isinstance(items, list) or isinstance(items, str)):
            raise ValueError("items必须是字符串列表或字符串(动态菜单)")

        if isinstance(items, list):
            if not all(isinstance(item, str) for item in items):
                raise ValueError("所有菜单选项必须是字符串")
            if not items:
                raise ValueError("菜单选项不能为空")

        self.menus[name] = {
            'id': f'menu_{self.current_menu_id}',
            'name': name,
            'acceptReporters': accept_reporters,
            'items': items if not dynamic else None,
            'dynamic': items if dynamic else None
        }
        self.current_menu_id += 1

    def add_js_function(self, js_code: str) -> None:
        """添加自定义JavaScript函数"""
        self.js_functions.append(js_code)

    def build_extension(self,
                       ext_id: str,
                       ext_name: str,
                       ext_color: Optional[str] = None,
                       ext_menu_icon: Optional[str] = None,
                       ext_block_icon: Optional[str] = None,
                       ext_docs: Optional[str] = None) -> str:
        """
        生成Scratch扩展的JavaScript代码
        
        参数:
            ext_id: 扩展的唯一ID(英文)
            ext_name: 扩展的显示名称
            ext_color: 扩展颜色(十六进制)
            ext_icon: 扩展图标的DataURL
            ext_docs: 扩展文档URL
            
        返回:
            生成的JavaScript代码
            
        异常:
            RuntimeError: 如果生成过程中出错
        """
        if not self.blocks:
            raise RuntimeError("至少需要定义一个积木块")

        # 更新扩展元数据
        if ext_id is not None:
            self.extension_meta['id'] = ext_id
        if ext_name is not None:
            self.extension_meta['name'] = ext_name
        if ext_color is not None:
            self.extension_meta['color1'] = ext_color
        if ext_block_icon is not None:
            self.extension_meta['blockIconURI'] = ext_block_icon
        if ext_menu_icon is not None:
            self.extension_meta['menuIconURI'] = ext_menu_icon
        if ext_docs is not None:
            self.extension_meta['docs'] = ext_docs

        try:
            # 生成扩展基本信息
            js_code = f"""(function(Scratch) {{
    {'\n    '.join(self.imports)}
    
    // 全局变量
    {'\n    '.join(self.global_vars)}
    
    class {self.extension_meta['id'].capitalize()} {{
        getInfo() {{
            return {{
                id: "{self.extension_meta['id']}",
                name: "{self.extension_meta['name']}",
                color1: "{self.extension_meta['color1']}",
                blockIconURI: "{self.extension_meta['blockIconURI']}",
                blockMenuURI: "{self.extension_meta['menuIconURI']}",
                docsURI: "{self.extension_meta['docs']}",
                blocks: [
"""

            # 添加所有积木定义
            block_defs = []
            for block in self.blocks:
                block_def = f"                    {{\n"
                block_def += f"                        {'opcode' if block['type'].upper() != 'BUTTON' else 'func'}: \"{block['opcode']}\",\n"
                block_def += f"                        blockType: Scratch.BlockType.{block['type'].upper()},\n"
                block_def += f"                        text: \"{block['text']}\",\n"
                
                # 处理参数
                if block['args']:
                    block_def += "                        arguments: {\n"
                    arg_lines = []
                    for arg_name, arg_config in block['args'].items():
                        arg_line = f"                            {arg_name}: {{\n"
                        for key, value in arg_config.items():
                            if isinstance(value, str):
                                arg_line += f"                                {key}: \"{value}\",\n"
                            else:
                                arg_line += f"                                {key}: {json.dumps(value)},\n"
                        arg_line += "                            }"
                        arg_lines.append(arg_line)
                    block_def += ',\n'.join(arg_lines) + "\n"
                    block_def += "                        },\n"
                
                # 添加特殊属性
                if 'showIn' in block:
                    block_def += f"                        filter: {json.dumps(block['showIn'])},\n"
                if 'isTerminal' in block:
                    block_def += f"                        isTerminal: {json.dumps(block['isTerminal'])},\n"
                
                block_def = block_def.rstrip(',\n') + "\n"
                block_def += "                    }"
                block_defs.append(block_def)

            js_code += ',\n'.join(block_defs)
            js_code += "\n                ],\n"

            # 添加菜单定义(如果有)
            if self.menus:
                js_code += "                menus: {\n"
                menu_defs = []
                for menu_name, menu in self.menus.items():
                    menu_def = f"                    {menu_name}: {{\n"
                    menu_def += f"                        acceptReporters: {json.dumps(menu['acceptReporters'])},\n"
                    if menu['dynamic']:
                        menu_def += f"                        items: \"{menu['dynamic']}\"\n"
                    else:
                        menu_def += f"                        items: {json.dumps(menu['items'])}\n"
                    menu_def += "                    }"
                    menu_defs.append(menu_def)
                
                js_code += ',\n'.join(menu_defs)
                js_code += "\n                },\n"

            # 添加扩展元信息
            js_code += f"""
            }};
        }}
"""

            # 添加自定义JS函数
            for func in self.js_functions:
                js_code += f"\n    {func}\n"

            # 添加积木对应的JavaScript函数
            for block in self.blocks:
                if block['type'] == 'label':
                    continue
                # 为JS代码添加适当缩进
                indented_js = '\n'.join('            ' + line if line.strip() else line for line in block['js_code'].split('\n'))
                js_code += f"""
        {block['opcode']}(args) {{
{indented_js}
        }}
"""

            js_code += f"""    }}
    Scratch.extensions.register(new {self.extension_meta['id'].capitalize()}());
}})(Scratch);"""
            
            return js_code

        except Exception as e:
            raise RuntimeError(f"生成扩展代码时出错: {str(e)}")
