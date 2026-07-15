# Invalid keyed-task Execution Graph regression fixture

This reproduces the model-emitted graph shape reported after v1.6.7. It is valid YAML but invalid
against Leanforge's Execution Graph contract because `tasks` is missing and the task is used as a
top-level key instead of a list item with an `id` field.

```yaml
task_1:
  depends: []
  risk: RISKY
regen_barriers: []
```
