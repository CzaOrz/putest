# coding: utf-8
import os
import sys
import loggus
import inspect
import colorama
import importlib

from datetime import datetime
from threading import RLock


class Collector:
    allSample = 0
    passSample = 0
    failSample = 0
    lock = RLock()

    def add(self):
        with self.lock:
            self.allSample += 1

    def addPass(self):
        with self.lock:
            self.passSample += 1
            self.add()

    def addFail(self):
        with self.lock:
            self.failSample += 1
            self.add()

    def show(self):
        print("\r\n --------------- \r\n")
        print(f"用例总量: {self.allSample}")
        print(f"成功:{self.passSample}")
        print(f"失败:{self.failSample}")
        if self.failSample:
            print(colorama.Fore.RED + f"测试不通过")
            sys.exit(50)
        else:
            print(colorama.Fore.GREEN + f"测试通过")
            sys.exit(0)


collector = Collector()


class PUTLogger(loggus.Logger):
    pass


class CollectorInfoHook(loggus.IHook):

    def GetLevels(self):
        return [loggus.INFO]

    def ProcessMsg(self, msg):
        collector.addPass()


class CollectorErrorHook(loggus.IHook):

    def GetLevels(self):
        return [loggus.ERROR]

    def ProcessMsg(self, msg):
        collector.addFail()


logger = loggus.NewLogger()
logger.AddHook(CollectorInfoHook())
logger.AddHook(CollectorErrorHook())
entry = loggus.NewEntry(logger)

template = f"""
import loggus

from .{'moduleName'} import *
"""
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


def create():
    pass


def scan():
    for path, dirs, files in os.walk("."):
        for file in files:
            if not file.endswith("_test.py"):
                continue
            module = os.path.join(path, file). \
                replace(".\\", ""). \
                replace("\\", "."). \
                replace(".py", "")
            try:
                log = entry.withField("module", module)
                module = importlib.import_module(module)
                for attr in dir(module):
                    if attr.startswith("UnitTest_"):
                        getattr(module, attr)(log)
            except:
                entry.withTraceback().panic("TestErr")
    collector.show()


if __name__ == '__main__':
    scan()
