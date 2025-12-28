from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import secrets
import json

app = Flask(__name__)
app.secret_key = 'super-secret-demo-key'  # For session management

# --- IN-MEMORY STORAGE (For Demo Purposes) ---
# Structure: { 'username': {'id': 1, 'share_x': 1, 'share_y': 12345...} }
USERS_DB = {}
# Global variable to store the "reconstruction session" state
RECONSTRUCTION_POOL = [] 

# --- SHAMIR'S ALGORITHM LOGIC ---
PRIME = 2**127 - 1

def text_to_int(text):
    hex_val = text.encode('utf-8').hex()
    return int(hex_val, 16)

def int_to_text(number):
    hex_val = hex(number)[2:]
    if len(hex_val) % 2 != 0:
        hex_val = '0' + hex_val
    try:
        return bytes.fromhex(hex_val).decode('utf-8')
    except:
        return "[Error: Decryption Failed]"

def eval_poly(poly, x):
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % PRIME
    return accum

def split_secret(secret_text, n, k):
    secret_int = text_to_int(secret_text)
    if secret_int >= PRIME:
        raise ValueError("Secret too long for demo prime.")
    
    coefs = [secret_int] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    shares = []
    for x in range(1, n + 1):
        y = eval_poly(coefs, x)
        shares.append((x, y))
    return shares

def recover_secret(shares_list):
    # shares_list format: [(x1, y1), (x2, y2), ...]
    if not shares_list: return ""
    
    x_s, y_s = zip(*shares_list)
    secret = 0
    k = len(shares_list)
    
    for j in range(k):
        numerator, denominator = 1, 1
        for m in range(k):
            if j == m: continue
            numerator = (numerator * (-x_s[m])) % PRIME
            denominator = (denominator * (x_s[j] - x_s[m])) % PRIME
        
        inv = pow(denominator, -1, PRIME)
        lagrange = (numerator * inv) % PRIME
        secret = (secret + y_s[j] * lagrange) % PRIME
        
    return int_to_text(secret)

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('home.html')

# --- ADMIN FLOW ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        secret = request.form.get('secret')
        usernames = request.form.get('usernames').split(',')
        threshold = int(request.form.get('threshold'))
        
        usernames = [u.strip() for u in usernames if u.strip()]
        n = len(usernames)
        
        if n < threshold:
            return "Error: Threshold cannot be higher than user count!"

        # Generate Shares
        try:
            shares = split_secret(secret, n, threshold)
        except ValueError as e:
            return str(e)

        # Assign to Users DB
        global USERS_DB
        USERS_DB = {} # Reset DB
        for i, username in enumerate(usernames):
            # Share format: (x, y). x is index+1
            USERS_DB[username] = {
                'x': shares[i][0],
                'y': str(shares[i][1]) # Store as string to avoid JS precision issues
            }
        
        return redirect(url_for('admin_success'))
        
    return render_template('admin.html')

@app.route('/admin/success')
def admin_success():
    return f"<h3>Secret Split Successfully!</h3><p>Users created: {', '.join(USERS_DB.keys())}</p><a href='/'>Go Home</a>"

# --- USER FLOW ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username in USERS_DB:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return "User not found!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    
    username = session['user']
    user_data = USERS_DB.get(username)
    return render_template('dashboard.html', user=username, share=user_data)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# --- RECONSTRUCTION FLOW ---
@app.route('/reconstruct', methods=['GET'])
def reconstruct_ui():
    return render_template('reconstruct.html')

@app.route('/api/pool', methods=['GET', 'POST', 'DELETE'])
def pool_handler():
    # Helper API to manage the 'pool' of submitted shares
    global RECONSTRUCTION_POOL
    
    if request.method == 'POST':
        data = request.json
        # Check if already added
        if not any(s['x'] == data['x'] for s in RECONSTRUCTION_POOL):
            RECONSTRUCTION_POOL.append(data)
        return jsonify({'status': 'ok', 'pool': RECONSTRUCTION_POOL})
        
    elif request.method == 'DELETE':
        RECONSTRUCTION_POOL = []
        return jsonify({'status': 'cleared'})
        
    return jsonify(RECONSTRUCTION_POOL)

@app.route('/api/solve', methods=['POST'])
def solve():
    # Attempt to solve with current pool
    shares = [(s['x'], int(s['y'])) for s in RECONSTRUCTION_POOL]
    try:
        result = recover_secret(shares)
        return jsonify({'success': True, 'secret': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)