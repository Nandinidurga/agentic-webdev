import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Agentic IDE - Full-Stack AI Web Engineering Studio",
  description: "Autonomous full-stack web application development studio powered by multi-agent LangGraph, Sandpack live preview, and Node.js Express REST APIs.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cryptoPolyfillScript = `
    (function() {
      if (typeof window === 'undefined') return;
      if (!window.crypto) window.crypto = {};
      if (!window.crypto.subtle || typeof window.crypto.subtle.digest !== 'function') {
        function sha256(bytes) {
          var K = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
          ];
          var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
          var b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
          var bitLen = b.length * 8;
          var newLen = ((b.length + 8 >> 6) + 1) << 6;
          var p = new Uint8Array(newLen);
          p.set(b);
          p[b.length] = 0x80;
          var v = new DataView(p.buffer);
          v.setUint32(newLen - 4, bitLen >>> 0);
          v.setUint32(newLen - 8, Math.floor(bitLen / 0x100000000));
          var W = new Uint32Array(64);
          for (var i = 0; i < newLen; i += 64) {
            for (var t = 0; t < 16; t++) W[t] = v.getUint32(i + t * 4);
            for (var t = 16; t < 64; t++) {
              var s0 = ((W[t-15] >>> 7) | (W[t-15] << 25)) ^ ((W[t-15] >>> 18) | (W[t-15] << 14)) ^ (W[t-15] >>> 3);
              var s1 = ((W[t-2] >>> 17) | (W[t-2] << 15)) ^ ((W[t-2] >>> 19) | (W[t-2] << 13)) ^ (W[t-2] >>> 10);
              W[t] = (W[t-16] + s0 + W[t-7] + s1) | 0;
            }
            var a = H[0], b_ = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
            for (var t = 0; t < 64; t++) {
              var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
              var ch = (e & f) ^ (~e & g);
              var temp1 = (h + S1 + ch + K[t] + W[t]) | 0;
              var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
              var maj = (a & b_) ^ (a & c) ^ (b_ & c);
              var temp2 = (S0 + maj) | 0;
              h = g; g = f; f = e; e = (d + temp1) | 0; d = c; c = b_; b_ = a; a = (temp1 + temp2) | 0;
            }
            H[0] = (H[0] + a) | 0; H[1] = (H[1] + b_) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
            H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
          }
          var res = new ArrayBuffer(32);
          var out = new DataView(res);
          for (var j = 0; j < 8; j++) out.setUint32(j * 4, H[j]);
          return res;
        }
        var subtleObj = {
          digest: function(algo, data) {
            return Promise.resolve(sha256(data));
          }
        };
        try {
          Object.defineProperty(window.crypto, 'subtle', { value: subtleObj, configurable: true, writable: true });
        } catch(e) {
          window.crypto.subtle = subtleObj;
        }
      }
    })();
  `;

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: cryptoPolyfillScript }} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
