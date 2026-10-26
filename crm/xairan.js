// Helper function to compute modular inverse using Extended Euclidean Algorithm
// Returns the modular inverse of 'a' modulo 'm', where 'a' and 'm' are BigInts
function modInverse(a, m) {
    let m0 = m;
    let y = 0n;
    let x = 1n;
    if (m === 1n) return 0n;
    while (a > 1n) {
        let q = a / m;
        let t = m;
        m = a % m;
        a = t;
        t = y;
        y = x - q * y;
        x = t;
    }
    if (x < 0n) x += m0;
    return x;
}

// Constants
const a = 3n; // Fixed odd BigInt for transformation
const m = 2n ** 64n; // Modulus (2^64)
const b = modInverse(a, m); // Modular inverse of 'a' modulo 'm'
const alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'; // Base 62 alphabet

// Helper function to convert BigInt to base 62 string
// Takes a BigInt 'n' and desired length (default 11), returns padded base 62 string
function toBase62(n, length = 11) {
    if (n === 0n) return alphabet[0].repeat(length); // Handle zero case
    let s = '';
    while (n > 0n) {
        const r = Number(n % 62n);
        s = alphabet[r] + s;
        n = n / 62n;
    }
    return s.padStart(length, alphabet[0]); // Pad with '0's to fixed length
}

// Helper function to convert base 62 string to BigInt
// Takes a base 62 string 's', returns corresponding BigInt
function fromBase62(s) {
    let n = 0n;
    for (let char of s) {
        const index = alphabet.indexOf(char);
        if (index === -1) throw new Error('Invalid character in string');
        n = n * 62n + BigInt(index);
    }
    return n;
}

// Function to encode integer to random-looking string
// Takes a non-negative integer 'x', returns 11-character random-looking string
function parseIntToRandomString(x) {
    x = parseInt(x, 10);
    // Input validation
    if (typeof x !== 'number' || !Number.isInteger(x) || x < 0) {
        throw new Error('Input must be a non-negative integer');
    }
    const xBig = BigInt(x); // Convert to BigInt for precision
    // Apply transformation: y = (a * x) mod m
    const y = (a * xBig) % m;
    // Convert to base 62 string
    return toBase62(y, 11);
}

// Function to decode random-looking string back to integer
// Takes an 11-character string 's', returns original integer
function parseRandomStringToInt(s) {
    // Input validation
    if (typeof s !== 'string' || s.length !== 11) {
        alert('Error fetching ticket. Please check the URL and try again.');
        throw new Error('Input must be a string of length 11');
    }
    // Convert base 62 string back to BigInt
    const y = fromBase62(s);
    // Apply inverse transformation: x = (b * y) mod m
    const xBig = (b * y) % m;
    const x = Number(xBig);
    // Check for overflow
    if (x > Number.MAX_SAFE_INTEGER) {
        alert('Error fetching ticket. Please check the URL and try again.');
        throw new Error('Decoded number is too large for JavaScript Number type');
        
    }
    return x;
}