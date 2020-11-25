# coding: utf-8
import os
import loggus
import inspect
import importlib

from datetime import datetime

funcTemplate = f"""
def UnitTest_{'funcName'}():
    entry = logger.withField("funcName", "add")

    samples = [
        {{
            "name": str,
            "parameters": [
                {'there is a dict'}
            ],
            "want": Any,
            "wantErr": bool,
        }},
        {{
            "name": "test",
            "parameters": [1, 2],
            "want": 3,
            "wantErr": False,
        }}
    ]
    for sample in samples[1:]:
        log = entry.withField("sampleName", sample["name"])
        want = None
        try:
            {'解析并执行函数'}
        except:
            if not sample["wantErr"]:
                log.withTraceback().error("ExceptionErr")
                continue
        if want != sample["want"]:
            log.withFields({{
                "want": sample["want"],
                "actual": want,
            }}).error("EqualErr")
            continue
        log.info("pass")
"""


def add(x, y):
    pass


def warning():
    pass


if __name__ == '__main__':
    import os
    import importlib

    for path, dirs, files in os.walk("."):
        for file in files:
            if not file.endswith("_test.py"):
                continue
            module = os.path.join(path, file).replace(".\\", "").replace("\\", ".").replace(".py", "")
            try:
                module = importlib.import_module(module)
                for attr in dir(module):
                    if attr.startswith("UnitTest_"):
                        getattr(module, attr)()
            except:
                import traceback

                print(traceback.format_exc())
