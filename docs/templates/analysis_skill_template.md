# Reference Template — Analysis Skill

Mẫu tham chiếu chuẩn thiết kế một tác nhân phân tích (Analysis Agent) trong hệ sinh thái AIWF.

```yaml
name: analysis-template
command: analyze
checkpoint: 3
```

## 1. Hợp đồng tích hợp SDK
```python
from hierarchical_runtime import HierarchicalRuntime

class AnalysisTemplate:
    def __init__(self):
        self.client = HierarchicalRuntime("ANALYSIS-AGENT")
```
