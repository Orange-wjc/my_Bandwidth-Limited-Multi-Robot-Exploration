# 事件触发式学习通信改进方案

## 1. 背景

原项目实现了面向带宽受限多机器人探索任务的 privileged reinforcement learning 和 learned communication。每个机器人会把自己的局部 belief graph 编码成一个固定长度的 learned message，并在每个决策步把这条消息广播给其他机器人。

相比直接共享 occupancy grid map，这种设计已经大幅降低了单条消息的大小。但是它仍然默认每个机器人在每个决策步都进行通信。在水下、地下、灾害救援等带宽受限或通信不稳定的场景中，这个假设仍然偏理想化。尤其当机器人连续几步的局部状态变化不大时，每一步都发送消息会造成通信资源浪费。

我们的改进思路是：保留原论文的 learned-message 表征方式，但让通信频率变成自适应的。

## 2. 核心思想

核心想法是：

> 机器人只有在当前 learned message 包含足够新的信息或足够重要的信息时，才发送新消息。

在原方法中，机器人 `i` 在第 `t` 步生成一条 learned message：

```text
m_i^t in R^64
```

原方法会在每一步直接广播 `m_i^t`。我们改为维护机器人 `i` 上一次真正发送出去的消息：

```text
\bar{m}_i
```

然后计算当前消息与上一次发送消息之间的差异：

```text
d_i^t = ||m_i^t - \bar{m}_i||_2
```

如果差异大于阈值 `tau`，说明机器人当前状态或局部信息发生了明显变化，于是发送新消息：

```text
if d_i^t > tau:
    send m_i^t
    \bar{m}_i = m_i^t
else:
    do not send
```

如果某个机器人没有收到队友的新消息，它就继续使用最近一次收到的旧消息。这个机制可以称为 stale-message memory，也就是“过期消息记忆”或“历史消息复用”。

## 3. 论文方向定位

建议中文题目：

```text
面向带宽受限多机器人探索的事件触发学习通信方法
```

建议英文题目：

```text
Event-Triggered Learned Communication for Bandwidth-Limited Multi-Robot Exploration
```

原论文主要解决的是：在固定每步通信协议下，机器人应该通信什么内容。我们的改进主要解决的是：在 learned message 已经存在的基础上，机器人应该什么时候通信。

可以提炼成以下贡献点：

1. 提出一种面向带宽受限多机器人探索的事件触发式 learned communication 机制。
2. 在基本保留原始策略网络和 learned-message 表征的前提下，进一步降低通信频率和通信量。
3. 在不同阈值、不同队伍规模、丢包率和通信延迟条件下，评估通信量与探索效率之间的 trade-off。

## 4. 对比方法

建议设置以下 baseline：

1. 原始 learned communication。
   每个机器人在每个决策步都发送 64 维 learned message。

2. 固定频率通信。
   机器人每隔 `k` 步通信一次，例如 `k = 2, 4, 8`。

3. 事件触发通信。
   机器人只有在消息变化超过阈值 `tau` 时才通信。

可选 baseline：

1. 无通信。
   机器人只使用自己的局部观测。

2. 随机通信。
   机器人在每一步以固定概率 `p` 通信。

3. 地图共享 baseline。
   如果代码和实验条件允许，可以和原论文中的显式地图共享方法比较。

## 5. 评价指标

主要指标：

1. 探索路径长度。
   与原论文保持一致，使用所有机器人中最大的 travel distance。

2. 成功率。
   判断团队是否能在最大 episode 步数内达到探索率阈值。

3. 最终探索率。
   记录 episode 结束时的 explored rate。

4. 上传通信量。
   每个机器人发送的数据总量。

5. 下载通信量。
   每个机器人接收的数据总量。

6. 通信次数。
   实际发送的消息数量。

建议消息大小计算方式：

```text
message_bytes = EMBEDDING_DIM * 4
```

默认设置下：

```text
EMBEDDING_DIM = 64
message_bytes = 64 * 4 = 256 bytes
```

如果一个机器人发送一条消息给所有其他机器人，则对于一次消息发送：

```text
upload_bytes += message_bytes
download_bytes += (n_agents - 1) * message_bytes
```

上传和下载的具体定义要和论文实验表格保持一致。关键是所有方法都使用同一套统计方式。

## 6. 实验设计

### 6.1 主实验

比较以下方法：

```text
Original per-step communication
Fixed-frequency communication, k = 2
Fixed-frequency communication, k = 4
Fixed-frequency communication, k = 8
Event-triggered communication
```

汇报指标：

```text
travel distance
success rate
explored rate
upload volume
download volume
communication count
```

预期结果：

事件触发通信应该比每步通信显著减少通信量；在相近通信预算下，它应该比固定频率通信表现更好，因为它不会在关键状态变化时被固定间隔限制住。

### 6.2 阈值消融实验

测试多个阈值：

```text
tau = 0.05, 0.1, 0.2, 0.4, 0.8
```

预期趋势：

1. `tau` 越小，通信越频繁，探索性能越接近原始每步通信方法。
2. `tau` 越大，通信越少，但探索路径长度可能变差，成功率也可能下降。
3. 中间某个阈值通常会形成较好的通信量与探索性能折中。

推荐画图：

```text
x-axis: communication volume
y-axis: travel distance
```

这张图可以展示类似 Pareto curve 的 trade-off。

### 6.3 丢包鲁棒性实验

测试时模拟随机丢包：

```text
drop_rate = 0.0, 0.1, 0.3, 0.5
```

当一条消息被丢弃时，接收方继续使用最近一次收到的旧消息。

预期结果：

stale-message memory 应该能让策略对丢包具备一定鲁棒性。若在训练或 fine-tuning 中加入通信 dropout，鲁棒性应进一步提升。

### 6.4 通信延迟鲁棒性实验

测试时模拟消息延迟到达：

```text
delay = 0, 1, 2, 4 steps
```

预期结果：

随着延迟增加，性能会下降，但应当是平滑退化，而不是突然崩溃。

### 6.5 队伍规模泛化实验

训练时使用：

```text
N_AGENTS = 4
```

测试时使用：

```text
TEST_N_AGENTS = 4, 6, 8
```

这和原论文中的设定一致，也能验证 cooperative decoder 对不同队友数量消息的适应能力。

## 7. 实现计划

### 7.1 参数

在 `parameter.py` 和 `test_parameter.py` 中加入通信相关参数：

```python
COMM_MODE = "event"  # "always", "fixed", "event", "random"
COMM_THRESHOLD = 0.2
COMM_INTERVAL = 4
COMM_PROB = 0.5
COMM_DROPOUT_RATE = 0.0
COMM_DELAY_STEPS = 0
MESSAGE_BYTES = EMBEDDING_DIM * 4
```

建议支持以下模式：

```text
always: 原始每步通信
fixed: 每隔 COMM_INTERVAL 步通信一次
event: 当消息变化超过 COMM_THRESHOLD 时通信
random: 每一步以 COMM_PROB 的概率通信
```

### 7.2 Agent 状态

在 `Agent` 中增加：

```python
self.last_sent_msg = None
self.last_received_msgs = [None for _ in range(self.n_agent)]
self.comm_count = 0
self.upload_bytes = 0
self.download_bytes = 0
```

当前代码里的 `self.msgs` 已经在存储接收到的消息。为了最小化改动，第一版可以继续复用 `self.msgs`，只修改消息发送逻辑。后续如果要让代码更清晰，可以再把它重构成专门的 stale-message buffer。

### 7.3 Worker 通信逻辑

主要修改文件：

```text
multi_agent_worker.py
test_worker.py
```

当前逻辑：

```python
self.send_msg(current_state_feature.detach(), robot.id)
```

建议改成：

```python
should_send = self.should_send_msg(robot, current_state_feature, step=i)
if should_send:
    self.send_msg(current_state_feature.detach(), robot.id)
else:
    self.reuse_last_msg(robot.id)
```

关键细节：

在调用 `get_stacked_msg()` 之前，每个接收方都必须已经拥有其他所有机器人的消息。因此第 0 步所有机器人必须无条件发送消息，不能进行事件触发过滤。

### 7.4 事件触发判断函数

建议实现函数：

```python
def should_send_msg(self, robot, msg, step):
    if COMM_MODE == "always":
        return True

    if robot.last_sent_msg is None:
        return True

    if COMM_MODE == "fixed":
        return step % COMM_INTERVAL == 0

    if COMM_MODE == "random":
        return np.random.rand() < COMM_PROB

    if COMM_MODE == "event":
        diff = torch.norm(msg.detach() - robot.last_sent_msg.to(msg.device), p=2)
        return diff.item() > COMM_THRESHOLD

    raise ValueError(f"Unknown COMM_MODE: {COMM_MODE}")
```

当消息真正被发送后，更新：

```python
robot.last_sent_msg = msg.detach().clone()
```

### 7.5 通信统计

在 `send_msg` 中更新统计量：

```python
sender.upload_bytes += MESSAGE_BYTES
sender.comm_count += 1

for receiver in self.robot_list:
    if receiver.id != robot_id:
        receiver.download_bytes += MESSAGE_BYTES
```

episode 结束时保存：

```python
self.perf_metrics["comm_count"] = sum(robot.comm_count for robot in self.robot_list)
self.perf_metrics["upload_bytes"] = sum(robot.upload_bytes for robot in self.robot_list)
self.perf_metrics["download_bytes"] = sum(robot.download_bytes for robot in self.robot_list)
```

为了和原论文表格对齐，也可以汇报 MB：

```python
upload_mb = upload_bytes / (1024 * 1024)
download_mb = download_bytes / (1024 * 1024)
```

### 7.6 训练策略

推荐按以下顺序推进：

1. 先只在测试阶段实现事件触发通信。
   这样可以检查预训练原模型是否能承受较低频率通信。

2. 再使用事件触发通信重新训练或 fine-tune。
   这样策略可以逐渐适应 stale message。

3. 最后在训练中加入丢包和延迟增强。
   这可以提高模型在真实通信受限环境中的鲁棒性。

不建议第一步就做 learned gate network。它看起来更“智能”，但会明显增加训练复杂度，也更容易不稳定。

## 8. 可选扩展：学习式通信门控

在规则版事件触发方法稳定之后，可以考虑引入 learned gate。

Gate 输入：

```text
[m_i^t, \bar{m}_i, |m_i^t - \bar{m}_i|]
```

Gate 输出：

```text
g_i^t = sigmoid(MLP(input))
```

通信决策：

```text
send if g_i^t > 0.5
```

加入通信代价后的 reward：

```text
r_total = r_exploration - beta * communication_cost
```

这个版本创新性更强，但风险也更高。建议把它作为后续增强版本，而不是第一阶段实现目标。

## 9. 风险与注意事项

1. 原始 actor 是在每步都有新消息的条件下训练的。直接测试 stale message 可能会导致性能下降，因此可能需要 fine-tuning。

2. 第 0 步每个机器人必须发送消息。否则 `get_stacked_msg()` 可能因为某些消息列表为空而报错。

3. 原代码中训练和测试使用不同 worker。通信逻辑修改需要同时同步到 `multi_agent_worker.py` 和 `test_worker.py`。

4. 测试时机器人数量可能和训练时不同。遍历机器人消息时应尽量使用 `self.n_agent`，不要硬编码全局 `N_AGENTS`。

5. 当前 `PolicyNet.merge_msg()` 会引用 `self.msg_merger`，但 `PolicyNet.__init__` 中没有定义 `self.msg_merger`。目前主训练和测试流程似乎没有调用该函数，所以暂时不影响运行。如果后续引入新的消息聚合模块，可以顺手清理这个问题。

## 10. 第一阶段最小目标

第一阶段目标应该尽量小，并且可以快速验证：

1. 增加通信参数。
2. 增加事件触发发送逻辑。
3. 保证第 0 步所有机器人都发送消息。
4. 没有新消息时复用旧消息。
5. 记录通信次数和通信字节数。
6. 使用多个阈值跑测试实验。

如果这个阶段跑通，就可以先得到第一张核心实验表：

```text
method | travel distance | success rate | upload MB | download MB | comm count
```

这张表可以成为后续改进论文的主干结果。
