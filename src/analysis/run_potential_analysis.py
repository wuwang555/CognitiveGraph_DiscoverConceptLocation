#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
运行四规模涌现研究，保存包含压缩势的详细结果，并生成压缩势分布图。
用于验证方案二中的连续度量指标。
"""

import sys
import os
import time
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import random
random.seed(42)
np.random.seed(42)
# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入所需模块
try:
    from experiments.emergence_study_fixed import EmergenceStudyFixed
except ImportError:
    print("错误：无法导入 EmergenceStudyFixed，请确认 experiments/emergence_study_fixed.py 存在")
    sys.exit(1)


def setup_logging():
    """配置日志"""
    Path("../../logs").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/potential_analysis_{timestamp}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def run_potential_analysis(logger):
    """运行四规模涌现研究，保存详细结果并分析压缩势"""
    scales = [51, 71, 91, 111]
    output_dir = Path("../../results/analysis/potential_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_stats = {}

    for scale in scales:
        logger.info(f"\n{'='*60}")
        logger.info(f"开始规模 {scale} 概念")
        logger.info('='*60)

        study = EmergenceStudyFixed()
        start_time = time.time()
        results = study.run_pure_emergence_experiment(
            num_individuals=3,
            max_iterations=10000,
            num_concepts=scale
        )
        elapsed = time.time() - start_time
        logger.info(f"规模 {scale} 运行完成，耗时 {elapsed:.1f} 秒")

        # 提取压缩势列表
        all_potentials = []
        for i, ind_result in enumerate(results):
            # 移除不可序列化的 universe 对象
            serializable = {k: v for k, v in ind_result.items() if k != 'universe'}
            # 保存每个个体的详细结果
            out_file = output_dir / f"emergence_{scale}_ind{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
            logger.info(f"个体 {i} 结果已保存至 {out_file}")

            # 提取压缩事件的压缩势
            observations = ind_result.get('observations', {})
            compressions = observations.get('natural_compressions', [])
            potentials = [c.get('compression_potential') for c in compressions if c.get('compression_potential') is not None]
            all_potentials.extend(potentials)
            logger.info(f"个体 {i} 压缩事件数: {len(compressions)}，有效压缩势数: {len(potentials)}")

        # 统计当前规模的压缩势
        if all_potentials:
            stats = {
                'count': len(all_potentials),
                'mean': float(np.mean(all_potentials)),
                'std': float(np.std(all_potentials)),
                'min': float(np.min(all_potentials)),
                'max': float(np.max(all_potentials)),
                'q25': float(np.percentile(all_potentials, 25)),
                'q50': float(np.median(all_potentials)),
                'q75': float(np.percentile(all_potentials, 75))
            }
        else:
            stats = {k: None for k in ['count','mean','std','min','max','q25','q50','q75']}
            stats['count'] = 0

        all_stats[str(scale)] = stats
        logger.info(f"规模 {scale} 压缩势统计: {stats}")

        # 绘制压缩势分布直方图
        if all_potentials:
            plt.figure(figsize=(8,5))
            plt.hist(all_potentials, bins=20, edgecolor='black', alpha=0.7)
            plt.xlabel('压缩势 Φ = 内部平均能耗 / 外部平均能耗')
            plt.ylabel('频次')
            plt.title(f'概念规模 {scale} 的压缩势分布')
            plt.grid(True, alpha=0.3)
            hist_file = output_dir / f"potential_dist_scale{scale}.png"
            plt.savefig(hist_file, dpi=150)
            plt.close()
            logger.info(f"分布图已保存至 {hist_file}")

    # 保存所有规模的统计摘要
    summary_file = output_dir / f"potential_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)
    logger.info(f"统计摘要已保存至 {summary_file}")

    # 绘制规模趋势图
    scales_list = [51,71,91,111]
    means = [all_stats[str(s)]['mean'] for s in scales_list if all_stats[str(s)]['mean'] is not None]
    counts = [all_stats[str(s)]['count'] for s in scales_list if all_stats[str(s)]['count']>0]

    if means:
        plt.figure(figsize=(8,5))
        plt.plot(scales_list[:len(means)], means, marker='o', linestyle='-', linewidth=2)
        plt.xlabel('概念规模')
        plt.ylabel('平均压缩势 Φ')
        plt.title('压缩势随概念规模的变化')
        plt.grid(True, alpha=0.3)
        trend_file = output_dir / "potential_trend.png"
        plt.savefig(trend_file, dpi=150)
        plt.close()
        logger.info(f"趋势图已保存至 {trend_file}")

    return all_stats


def main():
    logger = setup_logging()
    logger.info("="*80)
    logger.info("开始运行压缩势分析（方案二）")
    logger.info("="*80)
    stats = run_potential_analysis(logger)
    logger.info("\n分析完成，结果已保存至 results/potential_analysis/")
    logger.info("="*80)


if __name__ == "__main__":
    # 设置中文字体
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    main()