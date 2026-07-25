import pandas as pd
import numpy as np
import os
import time
from tqdm import tqdm

# Фиксируем сид для воспроизводимости
np.random.seed(42)

def clean_paths_fast(df):
    """Очистка путей: UUID, ID и query-параметры заменяются масками."""
    if 'RequestPath' not in df.columns:
        return df
    # Быстрая отсечка параметров запроса
    df['path_clean'] = df['RequestPath'].str.split('?').str[0]
    
    # Маскирование динамических частей пути
    uuid_regex = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    df['path_clean'] = df['path_clean'].str.replace(uuid_regex, '{uuid}', regex=True)
    df['path_clean'] = df['path_clean'].str.replace(r'/\d+', '/{id}', regex=True)
    
    prefixes = ['/api/v1', '/v1', '/reservations-api/v1', '/reservations-api']
    for p in prefixes:
        df['path_clean'] = df['path_clean'].str.replace(p, '', case=False, regex=False)
    
    df['path_clean'] = '/' + df['path_clean'].str.lstrip('/')
    return df

def fast_entropy(values):
    """Расчет энтропии Шеннона с защитой от ошибок плавающей запятой."""
    if len(values) <= 1: return 0.0
    _, counts = np.unique(values, return_counts=True)
    probs = counts / counts.sum()
    ent = -np.sum(probs * np.log2(probs + 1e-12))
    return max(0.0, ent)

def entropy_with_noise_fast(intervals, bins=20, noise_level=0.1):
    """Метод стохастического резонанса: боты ломаются на добавлении шума."""
    n = len(intervals)
    if n < 2: return 0.0, 0.0, 1.0

    m_int = np.mean(intervals)
    s_int = np.std(intervals)
    
    if s_int < 1e-6:
        h_orig = 0.0
        bin_edges = np.linspace(m_int * 0.9, m_int * 1.1, bins + 1)
    else:
        # Пытаемся построить гистограмму
        try:
            hist, bin_edges = np.histogram(intervals, bins=bins, density=True)
            p = hist / (hist.sum() + 1e-12)
            h_orig = -np.sum(p[p > 0] * np.log2(p[p > 0]))
        except:
            h_orig = 0.0
            bin_edges = bins

    noise = np.random.normal(0, noise_level * (m_int + 1e-6), size=n)
    noisy = np.clip(intervals + noise, 0.001, None)

    hist_n, _ = np.histogram(noisy, bins=bin_edges, density=True)
    p_n = hist_n / (hist_n.sum() + 1e-12)
    h_noisy = -np.sum(p_n[p_n > 0] * np.log2(p_n[p_n > 0]))

    h_orig = max(0.0, h_orig)
    h_noisy = max(0.0, h_noisy)
    
    ratio = h_noisy / h_orig if h_orig > 0.005 else (h_noisy * 50) 
    return h_orig, h_noisy, ratio

def calculate_bot_score(row):
    """Логика оценки: 0 (человек) -> 1 (бот)"""
    score = 0.0
    # 1. Автокорреляция
    if row['autocorr_lag1'] > 0.8: score += 0.5
    elif row['autocorr_lag1'] > 0.5: score += 0.2
    # 2. Скорость
    if row['mean_interval'] < 1.0: score += 0.3
    # 3. Монотонность (низкая энтропия)
    if row['endpoint_entropy'] < 0.8: score += 0.2
    # 4. Коэффициент вариации (низкий = таймер)
    if row['cv_interval'] < 0.5: score += 0.3
    return min(1.0, score)

def main(input_file):
    start_time = time.time()
    print(f"🚀 Загрузка {input_file}...")
    
    try:
        df = pd.read_csv(input_file, usecols=['timestamp', 'RequestPath', 'userId', 'ipAddress', 'RequestId'])
    except Exception as e:
        print(f"Ошибка чтения: {e}")
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    for col in ['userId', 'RequestId', 'ipAddress']:
        df[col] = df[col].astype('category')

    print("🛠 Очистка путей...")
    df = clean_paths_fast(df)

    print("📦 Группировка в операции...")
    ops = df.groupby(['userId', 'RequestId'], observed=True).agg(
        op_start=('timestamp', 'min'),
        num_logs=('timestamp', 'count'),
        endpoint=('path_clean', 'first'),
        ip=('ipAddress', 'first')
    ).reset_index().sort_values(['userId', 'op_start'])

    print("⏱ Расчет интервалов...")
    ops['interval'] = ops.groupby('userId', observed=True)['op_start'].diff().dt.total_seconds()

    features = []
    user_groups = ops.groupby('userId', observed=True)

    print(f"📊 Анализ {len(user_groups)} пользователей...")
    for user_id, group in tqdm(user_groups):
        intervals = group['interval'].dropna().values
        if len(intervals) < 3: continue
            
        endpoints = group['endpoint'].values
        
        # ПЕРЕХОДЫ - ИСПРАВЛЕНО: используем np.char.add вместо np.core.defchararray.add
        if len(endpoints) > 1:
            try:
                # Безопасный способ для новых версий NumPy
                e_str = endpoints.astype(str)
                trans = np.char.add(e_str[:-1], "->")
                trans = np.char.add(trans, e_str[1:])
                ent_trans = fast_entropy(trans)
            except:
                ent_trans = 0
        else:
            ent_trans = 0

        # Автокорреляция
        if np.std(intervals) < 1e-6:
            autocorr = 1.0 
        else:
            with np.errstate(all='ignore'):
                ac = np.corrcoef(intervals[:-1], intervals[1:])[0, 1]
                autocorr = ac if not np.isnan(ac) else 0

        h_orig, h_noisy, h_ratio = entropy_with_noise_fast(intervals)

        features.append({
            'userId': user_id,
            'ops_count': len(group),
            'mean_interval': np.mean(intervals),
            'cv_interval': np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else 0,
            'autocorr_lag1': autocorr,
            'endpoint_entropy': fast_entropy(endpoints),
            'transition_entropy': ent_trans,
            'entropy_ratio': h_ratio,
            'unique_ips': group['ip'].nunique()
        })

    if not features:
        print("Недостаточно данных для анализа (нужно минимум 4 операции на пользователя).")
        return

    features_df = pd.DataFrame(features)
    print("🤖 Скоринг...")
    features_df['bot_score'] = features_df.apply(calculate_bot_score, axis=1)
    features_df = features_df.sort_values('bot_score', ascending=False)
    
    out = 'final_bot_analysis_fixed.csv'
    features_df.to_csv(out, index=False)
    print(f"✅ Готово за {time.time() - start_time:.2f} сек. Результат в {out}")

if __name__ == '__main__':
    path = 'raw_request.csv' 
    if os.path.exists(path):
        main(path)
    else:
        print(f"Файл {path} не найден. Проверьте путь.")
