# text_JSQL
这个是提前构思的用来尝试连接决胜千里平台和大模型，从而用来实现决策的东西


构思一下代码框架：

规则智能体应该是独立的一个文件夹，包含agent.py等物，把和平台通信的东西也放到这个里面去。

“提取态势形成文本”应该是一个独立的功能模块，放一个文件夹里面。

“和大模型交互”应该是一个独立的功能模块，放一个文件夹里面。这个库本身不包含大模型，只管用。

然后再来个主函数把它们串起来，想必就是比较好的。原生多线程吧，上来就设计成异步的，以便人机混合。
异步是多个层级的，一方面大模型生成命令和平台推演应该是异步的，比如隔一定步数来一次。另一方面，人类干涉和大模型生成命令也应该是异步的。

-----------------------
TODO：
1，跑一把完全的，一整把先拉通，修bug。
2，进一步的态势描述，如“谁和谁正在交火”
3，地形的处理
4，集成其他LLM模型