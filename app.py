from flask import Flask, render_template, request, redirect, url_for, flash,g, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key1'  # Needed for flash messages

DATABASE = 'trades.db'

@app.before_request
def load_current_user():
    g.current_user = request.headers.get('X-Forwarded-User', 'Guest')
    # This is a placeholder for user authentication, replace with actual logic if needed
    # For example, you can set g.current_user based on session or token
    


@app.context_processor
def inject_user():
    from datetime import datetime
    return dict(current_user=g.get('current_user', 'Guest'), current_year=datetime.now().year)



def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection()

    # Read filters
    ticker = request.args.get('ticker')
    action = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = '''
        SELECT trades.*, tickers.ticker
        FROM trades
        JOIN tickers ON trades.ticker_id = tickers.id
        WHERE 1=1
    '''
    params = []

    if ticker:
        query += ' AND tickers.ticker = ?'
        params.append(ticker)

    if action:
        query += ' AND trades.action = ?'
        params.append(action)

    if date_from:
        query += ' AND trades.trade_date >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND trades.trade_date <= ?'
        params.append(date_to)

    query += ' ORDER BY trades.trade_date DESC'

    trades = conn.execute(query, params).fetchall()

    # Get tickers for filter dropdown
    tickers = conn.execute('SELECT DISTINCT ticker FROM tickers ORDER BY ticker').fetchall()

    conn.close()

    return render_template('index.html', trades=trades, tickers=tickers)


@app.route('/trade', methods=['GET', 'POST'])
def trade():
    user_id = 1  # TODO: Replace this with session-based user ID later

    conn = get_db_connection()
    tickers = conn.execute('SELECT * FROM tickers WHERE is_active = 1 ORDER BY ticker').fetchall()

    if request.method == 'POST':
        ticker_id = request.form['ticker_id']
        quantity = float(request.form['quantity'])
        price = float(request.form['price'])
        action = request.form['action']
        trade_date = request.form['date']

        conn.execute('''
            INSERT INTO trades (user_id, ticker_id, quantity, price, action, trade_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, ticker_id, quantity, price, action, trade_date))
        conn.commit()
        conn.close()
        return redirect(url_for('trades'))

    conn.close()
    return render_template('trade.html', tickers=tickers)


@app.route('/trade/<int:trade_id>/edit', methods=('GET', 'POST'))
def edit_trade(trade_id):
    conn = get_db_connection()
    trade = conn.execute('''
        SELECT trades.*, tickers.ticker 
        FROM trades 
        JOIN tickers ON trades.ticker_id = tickers.id 
        WHERE trades.id = ?
    ''', (trade_id,)).fetchone()

    if trade is None:
        flash('Trade not found!')
        return redirect(url_for('index'))

    if request.method == 'POST':
        trade_date = request.form['trade_date']
        action = request.form['action']
        quantity = request.form['quantity']
        price = request.form['price']
        fees = request.form['fees']
        note = request.form['note']

        conn.execute('''
            UPDATE trades
            SET trade_date = ?, action = ?, quantity = ?, price = ?, fees = ?, notes = ?
            WHERE id = ?
        ''', (trade_date, action, quantity, price, fees, note, trade_id))
        conn.commit()
        conn.close()
        flash('Trade updated successfully!')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_trade.html', trade=trade)


@app.route('/trade/<int:trade_id>/delete', methods=('POST', 'GET'))
def delete_trade(trade_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
    conn.commit()
    conn.close()
    flash('Trade deleted successfully!')
    return redirect(url_for('index'))

@app.route('/trades')
def trades():
    user_id = 1  # TODO: Replace this with session-based user ID later

    conn = get_db_connection()
    trades = conn.execute('''
        SELECT trades.*, tickers.ticker, tickers.name
        FROM trades
        JOIN tickers ON trades.ticker_id = tickers.id
        WHERE trades.user_id = ?
        ORDER BY trades.trade_date DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('trades.html', trades=trades)


@app.route('/positions')
def positions():
    conn = get_db_connection()
    positions = conn.execute('''
        SELECT 
            tickers.ticker,
            SUM(CASE WHEN trades.action = 'BUY' THEN trades.quantity ELSE -trades.quantity END) AS net_quantity,
            SUM(CASE WHEN trades.action = 'BUY' THEN (trades.price * trades.quantity + trades.fees) ELSE 0 END) /
            NULLIF(SUM(CASE WHEN trades.action = 'BUY' THEN trades.quantity ELSE 0 END), 0) AS avg_price
        FROM trades
        JOIN tickers ON trades.ticker_id = tickers.id
        GROUP BY tickers.ticker
        HAVING net_quantity > 0
        ORDER BY tickers.ticker
    ''').fetchall()
    conn.close()

    return render_template('positions.html', positions=positions)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    conn = get_db_connection()
    tickers = conn.execute('SELECT * FROM tickers ORDER BY ticker').fetchall()
    conn.close()
    return render_template('dashboard.html', tickers=tickers)

@app.route('/chart/<ticker>')
def chart(ticker):
    conn = get_db_connection()
    stock = conn.execute('SELECT * FROM tickers WHERE ticker = ?', (ticker,)).fetchone()

    if not stock:
        flash('Stock not found.')
        return redirect(url_for('dashboard'))

    ticker_id = stock['id']

    # Get OHLC and indicators
    data = conn.execute('''
        SELECT prices.date, prices.open, prices.high, prices.low, prices.close, indicators.rsi, indicators.vwma, indicators.macd, indicators.macd_signal
        FROM prices
        LEFT JOIN indicators ON prices.ticker_id = indicators.ticker_id AND prices.date = indicators.date
        WHERE prices.ticker_id = ?
        ORDER BY prices.date ASC
    ''', (ticker_id,)).fetchall()

    conn.close()

    # Prepare JSON for chart
    ohlc = []
    vwma = []
    for row in data:
        ohlc.append({'time': row['date'], 'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close']})
        if row['vwma']:
            vwma.append({'time': row['date'], 'value': row['vwma']})

    return render_template('chart.html', ticker=ticker, ohlc=ohlc, vwma=vwma)


@app.route('/performance')
def performance():
    conn = get_db_connection()
    trades = conn.execute('''
        SELECT tickers.ticker, trades.*
        FROM trades
        JOIN tickers ON trades.ticker_id = tickers.id
        ORDER BY trades.trade_date ASC
    ''').fetchall()

    conn.close()

    performance = {}
    for trade in trades:
        ticker = trade['ticker']
        if ticker not in performance:
            performance[ticker] = {'quantity': 0, 'cost': 0, 'realized_pnl': 0}

        pos = performance[ticker]

        if trade['action'] == 'BUY':
            pos['cost'] += trade['price'] * trade['quantity'] + trade['fees']
            pos['quantity'] += trade['quantity']
        elif trade['action'] == 'SELL' and pos['quantity'] > 0:
            avg_price = pos['cost'] / pos['quantity'] if pos['quantity'] else 0
            realized = (trade['price'] - avg_price) * trade['quantity'] - trade['fees']
            pos['realized_pnl'] += realized
            pos['cost'] -= avg_price * trade['quantity']
            pos['quantity'] -= trade['quantity']

    return render_template('performance.html', performance=performance)


@app.route('/portfolio')
def portfolio():
    user_id = 1  # Replace with session-based user ID later

    conn = get_db_connection()

    portfolio = conn.execute('''
        WITH position_data AS (
            SELECT t.ticker_id, tickers.ticker, tickers.name,
                   SUM(CASE WHEN t.action = 'BUY' THEN t.quantity ELSE -t.quantity END) AS total_quantity,
                   SUM(CASE WHEN t.action = 'BUY' THEN t.quantity * t.price ELSE -t.quantity * t.price END) AS total_cost
            FROM trades t
            JOIN tickers ON t.ticker_id = tickers.id
            WHERE t.user_id = ?
            GROUP BY t.ticker_id
            HAVING total_quantity > 0
        ),
        latest_prices AS (
            SELECT p.ticker_id, p.close
            FROM prices p
            INNER JOIN (
                SELECT ticker_id, MAX(date) AS max_date
                FROM prices
                GROUP BY ticker_id
            ) latest ON p.ticker_id = latest.ticker_id AND p.date = latest.max_date
        )
        SELECT pd.ticker, pd.name, pd.total_quantity, pd.total_cost / pd.total_quantity AS avg_cost,
               lp.close AS current_price,
               (lp.close - pd.total_cost / pd.total_quantity) * pd.total_quantity AS unrealized_pnl,
               pd.total_quantity * lp.close AS market_value
        FROM position_data pd
        JOIN latest_prices lp ON pd.ticker_id = lp.ticker_id
        ORDER BY pd.ticker
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template('portfolio.html', portfolio=portfolio)

@app.route('/cumulative_pnl')
def cumulative_pnl():
    conn = get_db_connection()

    trades = conn.execute('''
        SELECT trades.*, tickers.ticker
        FROM trades
        JOIN tickers ON trades.ticker_id = tickers.id
        ORDER BY trades.trade_date ASC
    ''').fetchall()

    conn.close()

    pnl_data = []
    position_tracker = {}
    cumulative_pnl = 0

    for trade in trades:
        ticker = trade['ticker']
        date = trade['trade_date']

        if ticker not in position_tracker:
            position_tracker[ticker] = {'quantity': 0, 'cost': 0}

        pos = position_tracker[ticker]

        if trade['action'] == 'BUY':
            pos['cost'] += trade['price'] * trade['quantity'] + trade['fees']
            pos['quantity'] += trade['quantity']
        elif trade['action'] == 'SELL' and pos['quantity'] > 0:
            avg_price = pos['cost'] / pos['quantity'] if pos['quantity'] else 0
            realized_pnl = (trade['price'] - avg_price) * trade['quantity'] - trade['fees']
            cumulative_pnl += realized_pnl
            pos['cost'] -= avg_price * trade['quantity']
            pos['quantity'] -= trade['quantity']

        pnl_data.append({'time': date, 'value': cumulative_pnl})

    return render_template('cumulative_pnl.html', pnl_data=pnl_data)

@app.route('/notifications')
def notifications():
    conn = get_db_connection()

    alerts = conn.execute('''
        SELECT a.id, s.ticker, a.indicator, a.operator, a.value, i.date, i.rsi, i.macd, i.macd_signal, p.close
        FROM alerts a
        JOIN tickers s ON a.ticker_id = s.id
        LEFT JOIN (
            SELECT ticker_id, MAX(date) as max_date
            FROM indicators
            GROUP BY ticker_id
        ) latest ON a.ticker_id = latest.ticker_id
        LEFT JOIN indicators i ON a.ticker_id = i.ticker_id AND latest.max_date = i.date
        LEFT JOIN (
            SELECT ticker_id, MAX(date) as max_date, close
            FROM prices
            GROUP BY ticker_id
        ) p ON a.ticker_id = p.ticker_id
    ''').fetchall()

    conn.close()

    triggered = []

    for alert in alerts:
        if alert['indicator'] == 'RSI' and alert['operator'] == '<' and alert['rsi'] < alert['value']:
            triggered.append(alert)
        elif alert['indicator'] == 'RSI' and alert['operator'] == '>' and alert['rsi'] > alert['value']:
            triggered.append(alert)
        elif alert['indicator'] == 'MACD' and alert['operator'] == 'crosses':
            if alert['macd'] > alert['macd_signal']:  # Simple bullish crossover detection
                triggered.append(alert)
        elif alert['indicator'] == 'PRICE' and alert['operator'] == '<' and alert['close'] < alert['value']:
            triggered.append(alert)
        elif alert['indicator'] == 'PRICE' and alert['operator'] == '>' and alert['close'] > alert['value']:
            triggered.append(alert)

    return render_template('notifications.html', alerts=triggered)


from datetime import datetime

@app.route('/alerts', methods=['GET', 'POST'])
def manage_alerts():
    conn = get_db_connection()

    if request.method == 'POST':
        ticker_id = request.form['ticker_id']
        indicator = request.form['indicator']
        operator = request.form['operator']
        value = request.form.get('value')  # Optional for crossovers

        conn.execute('''
            INSERT INTO alerts (ticker_id, indicator, operator, value, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (ticker_id, indicator, operator, value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return redirect(url_for('manage_alerts'))

    tickers = conn.execute('SELECT * FROM tickers ORDER BY ticker').fetchall()
    alerts = conn.execute('''
        SELECT alerts.*, tickers.ticker
        FROM alerts
        JOIN tickers ON alerts.ticker_id = tickers.id
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()

    return render_template('alerts.html', alerts=alerts, tickers=tickers)

@app.route('/delete_alert/<int:alert_id>')
def delete_alert(alert_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_alerts'))


@app.route('/tickers')
def tickers():
    conn = get_db_connection()
    tickers = conn.execute('SELECT * FROM tickers ORDER BY ticker').fetchall()
    conn.close()
    return render_template('tickers.html', tickers=tickers)


@app.route('/tickers/edit/<int:ticker_id>', methods=['GET', 'POST'])
def edit_ticker(ticker_id):
    conn = get_db_connection()
    ticker = conn.execute('SELECT * FROM tickers WHERE id = ?', (ticker_id,)).fetchone()

    if request.method == 'POST':
        new_ticker = request.form['ticker']
        name = request.form['name']
        sector = request.form['sector']
        is_active = 1 if 'is_active' in request.form else 0
        nazwa1 = request.form['nazwa1']

        conn.execute('''
            UPDATE tickers
            SET ticker = ?, name = ?, sector = ?, is_active = ?, nazwa1 = ?
            WHERE id = ?
        ''', (new_ticker, name, sector, is_active, nazwa1, ticker_id))
        conn.commit()
        conn.close()
        return redirect(url_for('tickers'))

    conn.close()
    return render_template('edit_ticker.html', ticker=ticker)

@app.route('/charts')
def charts():
    user_id = 1  # TODO: Replace with session-based user ID later
    conn = get_db_connection()

    # Build performance time series
    performance_data = conn.execute('''
        WITH daily_positions AS (
            SELECT p.date, t.ticker, SUM(
                CASE WHEN tr.action = 'BUY' THEN tr.quantity
                     WHEN tr.action = 'SELL' THEN -tr.quantity
                END
            ) AS net_quantity
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.id
            JOIN trades tr ON tr.ticker_id = t.id
            WHERE tr.user_id = ?
            AND p.date >= tr.trade_date
            GROUP BY p.date, t.ticker
        )
        SELECT p.date, SUM(p.close * dp.net_quantity) AS portfolio_value
        FROM prices p
        JOIN tickers t ON p.ticker_id = t.id
        JOIN daily_positions dp ON dp.date = p.date AND dp.ticker = t.ticker
        GROUP BY p.date
        ORDER BY p.date
    ''', (user_id,)).fetchall()

    # Portfolio weights for pie chart
    weights_data = conn.execute('''
        WITH position_data AS (
            SELECT t.ticker_id, tickers.ticker, SUM(
                CASE WHEN t.action = 'BUY' THEN t.quantity ELSE -t.quantity END
            ) AS total_quantity
            FROM trades t
            JOIN tickers ON t.ticker_id = tickers.id
            WHERE t.user_id = ?
            GROUP BY t.ticker_id
            HAVING total_quantity > 0
        ),
        latest_prices AS (
            SELECT p.ticker_id, MAX(p.date) as latest_date
            FROM prices p
            GROUP BY p.ticker_id
        )
        SELECT tickers.ticker, p.close, pd.total_quantity,
               (p.close * pd.total_quantity) AS market_value
        FROM position_data pd
        JOIN tickers ON pd.ticker_id = tickers.id
        JOIN prices p ON pd.ticker_id = p.ticker_id
        JOIN latest_prices lp ON p.ticker_id = lp.ticker_id AND p.date = lp.latest_date
    ''', (user_id,)).fetchall()

    conn.close()

    # Prepare data for charts
    dates = [row['date'] for row in performance_data]
    portfolio_values = [row['portfolio_value'] for row in performance_data]

    labels = [row['ticker'] for row in weights_data]
    weights = [row['market_value'] for row in weights_data]

    return render_template('charts.html', dates=dates, portfolio_values=portfolio_values, labels=labels, weights=weights)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
