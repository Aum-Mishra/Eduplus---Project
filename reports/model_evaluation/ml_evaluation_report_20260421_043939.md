# EduPlus ML Model Evaluation Report

Generated at: 2026-04-21 04:39:38 UTC
Dataset: data/campus_placement_dataset_final_academic_4000.csv
Rows loaded: 4000

## placement_model
- samples: 4000
- accuracy: 0.911250
- precision: 0.887423
- recall: 0.942000
- f1: 0.913898
- roc_auc: 0.970864
- log_loss: 0.212337

## salary_model
- available: True
- samples: 2000
- mae: 2.133177
- rmse: 2.914006
- r2: 0.905432
- mape_percent: 31.026409

## job_role_model
- available: True
- samples: 2000
- num_classes_seen: 4
- accuracy: 0.982500
- f1_macro: 0.990402
- f1_weighted: 0.982504

## company_recommendation_model
- available: True
- samples: 2000
- top_k: 5
- hit_rate_at_k: 0.327500
- mrr_at_k: 0.158608

## salary_tier_model
- available: True
- samples: 2000
- num_classes_seen: 7
- accuracy: 0.829000
- f1_macro: 0.893264
- f1_weighted: 0.800455
- log_loss: 0.433510
