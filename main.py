import secrets
import functools

# A large prime number (Mersenne prime 2^127 - 1)
# This must be larger than the secret itself.
PRIME = 2**127 - 1

def _eval_poly(poly, x, prime):
    """Evaluates the polynomial at x using Horner's method."""
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % prime
    return accum

def _extended_gcd(a, b):
    """Returns (g, x, y) such that a*x + b*y = g = gcd(a, b)"""
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        q, b, a = b // a, a, b % a
        y0, y1 = y1, y0 - q * y1
        x0, x1 = x1, x0 - q * x1
    return b, x0, y0

def _mod_inverse(k, prime):
    """Compute the modular multiplicative inverse of k modulo prime."""
    # For prime p, inverse is k^(p-2) mod p, or use extended GCD
    # Python 3.8+ supports pow(k, -1, prime) directly
    return pow(k, -1, prime)

def split_secret(secret, n, k, prime=PRIME):
    """
    Splits a secret into n shares, and requires k shares to reconstruct.
    
    Args:
        secret (int): The integer secret to split.
        n (int): Total number of shares to generate.
        k (int): Minimum number of shares required to reconstruct.
        prime (int): The prime modulus for finite field arithmetic.
        
    Returns:
        List of tuples: [(1, share1), (2, share2), ...]
    """
    if secret >= prime:
        raise ValueError(f"Secret is too large for the current prime modulus.")

    # 1. Generate random coefficients for the polynomial
    # f(x) = secret + a1*x + a2*x^2 + ... + a(k-1)*x^(k-1)
    coefs = [secret] + [secrets.randbelow(prime) for _ in range(k - 1)]

    # 2. Generate shares (points on the polynomial)
    shares = []
    for x in range(1, n + 1):
        y = _eval_poly(coefs, x, prime)
        shares.append((x, y))
        
    return shares

def recover_secret(shares, prime=PRIME):
    """
    Recovers the secret from a list of shares using Lagrange Interpolation.
    
    Args:
        shares (list): A list of k tuples [(x1, y1), (x2, y2), ...].
        prime (int): The prime modulus used during splitting.
        
    Returns:
        int: The reconstructed secret.
    """
    if len(shares) < 1:
        raise ValueError("No shares provided.")
        
    x_s, y_s = zip(*shares)
    secret = 0

    # Lagrange Interpolation at x=0
    for j in range(len(shares)):
        numerator = 1
        denominator = 1
        
        for m in range(len(shares)):
            if j == m:
                continue
            
            # Compute basis polynomial L_j(0)
            # L_j(0) = product( -x_m / (x_j - x_m) ) for m != j
            numerator = (numerator * (-x_s[m])) % prime
            denominator = (denominator * (x_s[j] - x_s[m])) % prime
            
        # Add contribution of this share
        lagrange_coeff = (numerator * _mod_inverse(denominator, prime)) % prime
        secret = (secret + y_s[j] * lagrange_coeff) % prime

    return secret

# --- Example Usage ---

# 1. Define the secret (must be an integer)
my_secret = 123456789
print(f"Original Secret: {my_secret}")

# 2. Configuration: 5 shares total, 3 needed to recover
TOTAL_SHARES = 5
THRESHOLD = 3

# 3. Split the secret
shares = split_secret(my_secret, TOTAL_SHARES, THRESHOLD)
print(f"\nGenerated {TOTAL_SHARES} shares:")
for share in shares:
    print(f"  Share {share[0]}: {share[1]}")

# 4. Attempt recovery with partial shares
# Let's take the last 3 shares
subset_shares = shares[-3:] 

recovered = recover_secret(subset_shares)
print(f"\nRecovered Secret from 3 shares: {recovered}")

# Verification
assert recovered == my_secret
print("Success! The secret matches.")
