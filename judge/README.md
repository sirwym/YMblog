### go-judge 1.11.3


sudo ./go-judge \
  -http-addr "127.0.0.1:5050" \
  -enable-mount \
  -mount-conf mount.yaml \
  -parallelism 4 \
  -pre-fork 1 \
  -tmp-fs-param "size=128m,nr_inodes=4k" \
  -log-level warn \
  -auth-token "STRONG_TOKEN"

sudo ./go-judge_macOS \
  -http-addr "127.0.0.1:5050" \
  -mount-conf mount.yaml \
  -parallelism 4 \
  -pre-fork 1 \
  -tmp-fs-param "size=128m,nr_inodes=4k" \
  -release \
  -auth-token "STRONG_TOKEN" \
  -src-prefix "/"


go-judge部署  不使用docker 直接裸跑

1. 在线C++工具使用
   - 小数据(直接写到输入框的非常小的数据) 直接请求 go-judge编译运行 并返回结果 （这个我考虑不使用文件copy了）
   - 大数据(上传到media目录后， copy到dev/shm/go-judge) -> celery ->  go-judge直接获取文件id 编译运行，并返回
   
2. AI测试点生成
   - 通过ai生成gen.py（这个我考虑使用agent做决策）， 最后点击运行测试点生成数据
	- 问题描述/标程 -> celery -> openai -> gen.py/val.py
   - 关于gen.py  因为是裸跑go-judge , python可以使用一些库，例如cyaron, 数学库， 还有一些自己定制的killer_templates
	- gen.py/val.py -> go-judge -> 运行go-judge生成测试点 ->运行挂载内置的drive.py校验写入数据 -> 运行sol.cpp生成结果
	
https://github.com/luogu-dev/cyaron



	1.	go-judge 永远无状态
	2.	Host 文件系统是唯一真实数据源
	3.	小数据 → stdin/stdout
	4.	大数据 → bind mount + 文件
	5.	动态任务 → 每次 run 挂载
	6.	静态环境 → mount.yaml
	7.	stdout > 10MB → 不进 JSON



# 生产模式
docker compose up -d

# 开发模式（覆盖）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d