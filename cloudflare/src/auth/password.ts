/**
 * ProspectOS Cloudflare Serverless - WebCrypto PBKDF2 Password Verifier
 * 100% compatible with Python's hashlib.pbkdf2_hmac("sha256", password, salt, 100000)
 */

function bufToHex(buffer: ArrayBuffer): string {
  const byteArr = new Uint8Array(buffer);
  let hex = "";
  for (let i = 0; i < byteArr.length; i++) {
    hex += byteArr[i].toString(16).padStart(2, "0");
  }
  return hex;
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

export async function hashPassword(plainPassword: string): Promise<string> {
  const saltBytes = new Uint8Array(16);
  crypto.getRandomValues(saltBytes);
  const salt = bufToHex(saltBytes.buffer);

  const enc = new TextEncoder();
  const passwordKey = await crypto.subtle.importKey(
    "raw",
    enc.encode(plainPassword),
    { name: "PBKDF2" },
    false,
    ["deriveBits"]
  );

  const derivedBits = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt: enc.encode(salt),
      iterations: 100000,
      hash: "SHA-256",
    },
    passwordKey,
    256
  );

  const keyHex = bufToHex(derivedBits);
  return `${salt}$${keyHex}`;
}

export async function verifyPassword(plainPassword: string, storedHash: string): Promise<boolean> {
  try {
    const parts = storedHash.split("$");
    if (parts.length !== 2) return false;
    const [salt, expectedKeyHex] = parts;

    const enc = new TextEncoder();
    const passwordKey = await crypto.subtle.importKey(
      "raw",
      enc.encode(plainPassword),
      { name: "PBKDF2" },
      false,
      ["deriveBits"]
    );

    const derivedBits = await crypto.subtle.deriveBits(
      {
        name: "PBKDF2",
        salt: enc.encode(salt),
        iterations: 100000,
        hash: "SHA-256",
      },
      passwordKey,
      256
    );

    const checkKeyHex = bufToHex(derivedBits);
    return timingSafeEqual(checkKeyHex, expectedKeyHex);
  } catch {
    return false;
  }
}
