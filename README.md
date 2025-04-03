# NightPearl

一个基于纯adb命令行的自动化测试框架

## 执行测试用例

### 自动执行

直接执行`nightpearl.py`将自动寻找当前`testcase`目录下的所有`run.txt`文件进行解析

```txt
testcase01
#testcase02 3
testcase03 2
testcase04 -1
```

自动寻找并执行`testcase01.py`测试用例

通过`#`开头的行会被忽略

用例名后跟数字为执行次数，如果为负数则表示无限循环执行

### 手动执行用例

可通过如下命令手动执行

```shell
python nightpearl.py testcase01.py 2 testcase02.py
```

文件路径支持绝对路径和相对于`testcase`的路径

用例名后跟数字为执行次数，如果为负数则表示无限循环执行