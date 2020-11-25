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
def UnitTest_{'funcName'}(log: loggus.Entry):
    entry = log.withField("funcName", "add")

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


def create(py: str):
    py = py.replace(".py", "")
    try:
        module = importlib.import_module(py)
    except:
        loggus.withTraceback().panic("ImportModuleErr")
        return
    template = f"""# coding: utf-8
import loggus

from .{py} import *\n
"""
    for attr in dir(module):
        if attr.startswith(("_", "UnitTest")):
            continue
        attrIns = getattr(module, attr)
        if not inspect.isfunction(attrIns):
            continue
        sig = inspect.signature(attrIns)
        parameters = []
        argsKeys = []
        argsValues = []
        for k, v in sig.parameters.items():
            argsKeys.append(k)
            if v.kind == v.POSITIONAL_ONLY:
                argsValues.append(k)
            elif v.kind == v.POSITIONAL_OR_KEYWORD:
                argsValues.append(k)
            elif v.kind == v.VAR_POSITIONAL:
                argsValues.append(f"*{k}")
            elif v.kind == v.KEYWORD_ONLY:
                argsValues.append(f"**{k}")
            elif v.kind == v.VAR_KEYWORD:
                argsValues.append(f"**{k}")
            parameters.append("                {},".format({k: {"kind": v.kind.__str__()}}))
        argsKeys = ", ".join(argsKeys)
        if argsKeys:
            argsKeys += " = sample[\"parameters\"]"
        argsValues = ", ".join(argsValues)
        parameters = "\n".join(parameters)
        template += f"""
def UnitTest_{attr}(log: loggus.Entry):
    entry = log.withField("funcName", "{attr}")

    samples = [
        {{
            "name": str,
            "parameters": [
{parameters}
            ],
            "want": None,
            "wantErr": bool,
        }},
    ]
    for sample in samples[1:]:
        log = entry.withField("sampleName", sample["name"])
        want = None
        try:
            {argsKeys}
            want = {attr}({argsValues})
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
        log.info("pass")\n
"""
    with open(f"{py}_test.py", "w", encoding="utf-8") as f:
        f.write(template)


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


def execute():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", nargs="*", default=[])
    args = parser.parse_args()
    if len(args.cmd) == 0:
        return
    if args.cmd[0] == "test":
        scan()
    elif args.cmd[0] == "create" and len(args.cmd) > 1:
        create(args.cmd[1])


if __name__ == '__main__':
    # scan()
    create("temp.py")
