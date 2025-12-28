import secrets
import json

# --- Constants & Helpers ---
PRIME = 2**127 - 1

def text_to_int(text):
    """Converts a string to a large integer."""
    hex_val = text.encode('utf-8').hex()
    return int(hex_val, 16)

def eval_poly(poly, x, prime):
    """Evaluates the polynomial at x."""
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % prime
    return accum

def split_secret(secret_int, n, k, prime=PRIME):
    """Splits an integer into n shares with threshold k."""
    if secret_int >= prime:
        raise ValueError("Secret is too long! (Keep it under ~32 chars for this demo)")
        
    # Generate random coefficients: [secret, rand1, rand2, ...]
    coefs = [secret_int] + [secrets.randbelow(prime) for _ in range(k - 1)]
    
    shares = []
    for x in range(1, n + 1):
        y = eval_poly(coefs, x, prime)
        shares.append([x, y])
    return shares

# --- Main Execution ---
if __name__ == "__main__":
    print("=== SECRET SPLITTER ===")
    secret_input = input("Enter the secret message: ")
    n = int(input("How many total shares to generate? (n): "))
    k = int(input("How many shares needed to unlock? (k): "))

    try:
        secret_int = text_to_int(secret_input)
        shares = split_secret(secret_int, n, k)
        
        print("\n[SUCCESS] Here are your shares.")
        print("Copy the lines below (including brackets) to save them or give them to friends.")
        print("-" * 40)
        # We dump to JSON so it's easy to copy-paste into the next program
        print(json.dumps(shares, indent=2))
        print("-" * 40)
        
    except ValueError as e:
        print(f"Error: {e}")