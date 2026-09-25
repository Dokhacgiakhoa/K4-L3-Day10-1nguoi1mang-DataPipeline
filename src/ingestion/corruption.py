from __future__ import annotations

import pandas as pd


import json
import numpy as np

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str) -> pd.DataFrame:
    df_c = df.copy()
    logs = {}
    
    # 1. Drop 20% newest records
    df_c['published'] = pd.to_datetime(df_c['published'])
    df_c = df_c.sort_values(by='published', ascending=False)
    drop_count = int(len(df_c) * 0.2)
    dropped_ids = df_c.iloc[:drop_count]['paper_id'].tolist()
    df_c = df_c.iloc[drop_count:].copy()
    logs['scenario_1_drop_newest'] = {'affected_rows': drop_count, 'ids': dropped_ids}
    
    df_c = df_c.reset_index(drop=True)
    np.random.seed(42)
    indices = np.random.permutation(len(df_c))
    
    n10 = int(len(df_c) * 0.1)
    n20 = int(len(df_c) * 0.2)
    n5 = int(len(df_c) * 0.05)
    
    # 2. Blank summary (10%)
    idx_blank = indices[:n10]
    blank_ids = df_c.loc[idx_blank, 'paper_id'].tolist()
    df_c.loc[idx_blank, 'summary'] = ""
    logs['scenario_2_blank_summary'] = {'affected_rows': len(idx_blank), 'ids': blank_ids}
    
    # 3. Inject noise in summary (10%)
    idx_noise = indices[n10:2*n10]
    noise_ids = df_c.loc[idx_noise, 'paper_id'].tolist()
    df_c.loc[idx_noise, 'summary'] = df_c.loc[idx_noise, 'summary'].apply(lambda x: f"@@##$%$ {x} !@!#")
    logs['scenario_3_noise_summary'] = {'affected_rows': len(idx_noise), 'ids': noise_ids}
    
    # 4. Truncate title < 8 chars (10%)
    idx_trunc = indices[2*n10:3*n10]
    trunc_ids = df_c.loc[idx_trunc, 'paper_id'].tolist()
    df_c.loc[idx_trunc, 'title'] = df_c.loc[idx_trunc, 'title'].apply(lambda x: x[:7] if isinstance(x, str) else x)
    logs['scenario_4_truncate_title'] = {'affected_rows': len(idx_trunc), 'ids': trunc_ids}
    
    # 5. Shift published date by 365 days backwards (20%)
    idx_date = indices[3*n10:3*n10+n20]
    date_ids = df_c.loc[idx_date, 'paper_id'].tolist()
    df_c.loc[idx_date, 'published'] = df_c.loc[idx_date, 'published'] - pd.Timedelta(days=365)
    df_c.loc[idx_date, 'age_days'] = df_c.loc[idx_date, 'age_days'] + 365
    logs['scenario_5_shift_date'] = {'affected_rows': len(idx_date), 'ids': date_ids}
    
    # 6. Duplicate rows (5%)
    idx_dup = indices[3*n10+n20:3*n10+n20+n5]
    dup_df = df_c.loc[idx_dup].copy()
    dup_ids = dup_df['paper_id'].tolist()
    df_c = pd.concat([df_c, dup_df], ignore_index=True)
    logs['scenario_6_duplicate_rows'] = {'affected_rows': len(dup_df), 'ids': dup_ids}
    
    # 7. Rebuild text_for_embedding
    df_c['published'] = df_c['published'].dt.strftime('%Y-%m-%d')
    df_c['text_for_embedding'] = (
        "Title: " + df_c['title'].fillna('') + "\n" +
        "Authors: " + df_c['authors_joined'].fillna('') + "\n" +
        "Published: " + df_c['published'].fillna('') + "\n" +
        "Categories: " + df_c['categories_joined'].fillna('') + "\n" +
        "Summary: " + df_c['summary'].fillna('')
    )
    df_c['summary_chars'] = df_c['summary'].fillna('').apply(len)
    
    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    
    with open(output_log_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
        
    return df_c
