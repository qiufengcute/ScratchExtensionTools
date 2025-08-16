# Scratch Extension Tools

A Scratch Extension Tools.
It can help you made Scratch Extension.

## 📦 Installation
```bash
pip install ScratchExtensionTools
```

## 📜 Changelog
See [CHANGELOG.md](https://github.com/qiufengcute/ScratchExtensionTools/blob/main/CHANGELOG.md)


## QuickStart
```Python
from ScratchExtensionTools import ScratchExtensionBuilder

builder = ScratchExtensionBuilder()

def hello_func():
    print("Hello Scratch!")

builder.create_block(
    opcode="say_hello",
    block_type="command",
    text="say hello",
    py_func=hello_func,
    show_in=['sprites']  # Python side argument, exported as `filter` in Scratch JSON
)

js_code = builder.build_extension(
    ext_id="demo",
    ext_name="Demo Extension",
    ext_color="#ffcc00"
)

print(js_code)  # => Scratch JS Extension
```

## ⚠️ Note on filter / showin

In Scratch extension JSON, the property is filter.
But since filter is a Python built-in, this library uses the keyword showin on the Python side.
It will still output filter correctly in the generated Scratch extension JSON.
