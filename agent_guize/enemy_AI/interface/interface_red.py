# 这个是红方。直接不用写函数和类了。

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from interface import interface

runner_red = interface("red")

runner_red.run_redorblue()