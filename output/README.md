# Benchmark outputs

每次完整回归运行都保存在独立目录：

```text
output/<UTC运行时间>-run<GitHub运行序号>/
```

示例：

```text
output/20260825T135011Z-run12/
```

每个目录包含：

```text
0.json ... 111.json
summary.json
run_metadata.json
```

规则：

- 运行目录不可覆盖；
- 结果由 `benchmark/112-<运行时间>` 分支提交；
- 通过 Pull Request 合并到 `main`；
- 不在结果中记录 API Key；
- `summary.json` 只检查运行完整性，不代表官方数学 Judge 分数。
