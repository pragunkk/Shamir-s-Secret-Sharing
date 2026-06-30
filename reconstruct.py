import json

# --- Constants & Helpers ---
PRIME = 2**127 - 1

def int_to_text(number):
    """Converts the integer back to its original string."""
    hex_val = hex(number)[2:]
    if len(hex_val) % 2 != 0:
        hex_val = '0' + hex_val
    try:
        return bytes.fromhex(hex_val).decode('utf-8')
    except UnicodeDecodeError:
        return "??? (Decryption failed: Shares might be incorrect)"

def mod_inverse(a, prime):
    """Compute modular multiplicative inverse."""
    return pow(a, -1, prime)

def recover_secret(shares, prime=PRIME):
    """Recovers the secret using Lagrange Interpolation."""
    if not shares:
        return 0
        
    # Unpack the list of [x, y] lists
    x_s = [s[0] for s in shares]
    y_s = [s[1] for s in shares]
    
    secret = 0
    k = len(shares)

    for j in range(k):
        numerator = 1
        denominator = 1
        
        for m in range(k):
            if j == m:
                continue
            
            # Lagrange basis calculation
            numerator = (numerator * (-x_s[m])) % prime
            denominator = (denominator * (x_s[j] - x_s[m])) % prime
            
        lagrange_coeff = (numerator * mod_inverse(denominator, prime)) % prime
        secret = (secret + y_s[j] * lagrange_coeff) % prime

    return secret

# --- Main Execution ---
if __name__ == "__main__":
    print("=== SECRET RECONSTRUCTION ===")
    print("Paste your shares below as a JSON list (e.g., [[1, 234...], [3, 853...]]).")
    print("Press Enter.")
    
    user_input = input("Input Shares: ")
    
    try:
        shares = json.loads(user_input)
        
        print(f"\nProcessing {len(shares)} shares...")
        recovered_int = recover_secret(shares)
        recovered_text = int_to_text(recovered_int)
        
        print("-" * 40)
        print(f"RECONSTRUCTED SECRET: {recovered_text}")
        print("-" * 40)
        
    except json.JSONDecodeError:
        print("Error: Could not read input. Make sure it's valid format like [[1, 123], [2, 456]]")
    except Exception as e:
        print(f"Error: {e}")
