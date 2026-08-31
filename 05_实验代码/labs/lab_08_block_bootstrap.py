"""Lab 8: compare IID-like and dependence-aware confidence intervals."""

import numpy as np

from quantlearn.inference import moving_block_bootstrap_mean_ci

rng = np.random.default_rng(7)
returns = np.empty(1_000)
returns[0] = rng.normal(0.0003, 0.01)
for index in range(1, len(returns)):
    returns[index] = 0.35 * returns[index - 1] + rng.normal(0.0003, 0.01)

for block_size in (1, 5, 20):
    lower, upper = moving_block_bootstrap_mean_ci(
        returns, block_size=block_size, n_bootstrap=2_000, seed=42
    )
    print(
        f"block={block_size:>2}: mean={returns.mean():.5f}, "
        f"95% CI=[{lower:.5f}, {upper:.5f}]"
    )

print("\n块长度是研究假设；应结合依赖结构做敏感性分析。")
