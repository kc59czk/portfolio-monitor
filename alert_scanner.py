import sqlite3
import datetime

def scan_alerts():
    conn = sqlite3.connect('../stocks/stocks.db')
    conn.row_factory = sqlite3.Row
    today = datetime.date.today().isoformat()

    alerts = conn.execute('''
        SELECT a.*, t.ticker, i.rsi, p.volume, p.volume_avg_20
        FROM alerts a
        JOIN tickers t ON a.ticker_id = t.id
        JOIN indicators i ON i.ticker_id = t.id
        JOIN prices p ON p.ticker_id = t.id AND p.date = i.date
        WHERE a.is_active = 1 AND i.date = (SELECT MAX(date) FROM indicators WHERE ticker_id = t.id)
    ''').fetchall()

    for alert in alerts:
        context = {
            'rsi': alert['rsi'],
            'volume': alert['volume'],
            'volume_avg_20': alert['volume_avg_20'],
        }

        if any(v is None for v in context.values()):
            print(f"Skipping alert {alert['name']} for {alert['ticker']}: context contains None values {context}")
            continue

        try:
            condition_result = eval(alert['condition'], {}, context)
        except Exception as e:
            print(f"Invalid condition: {alert['condition']} → {e}")
            continue

        if condition_result:
            # Alert triggered
            print(f"[ALERT] {alert['name']} triggered for {alert['ticker']} (User {alert['user_id']})")

            conn.execute('''
                UPDATE alerts SET last_triggered = ? WHERE id = ?
            ''', (today, alert['id']))
            conn.commit()

    conn.close()

if __name__ == "__main__":
    scan_alerts()
