using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

public class CsvTranslator
{
    // ===== 설정 =====
    // !!! 배포 전 교체 !!!
    // Base64 32바이트 키 (AES-256). 예시: 32바이트 0x00
    private const string KEY_B64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    private static readonly byte[] KEY = Convert.FromBase64String(KEY_B64);
    private static readonly byte[] MAGIC = Encoding.ASCII.GetBytes("TCSV1");

    private const string PLAIN_NAME = "translation.csv";
    private const string ENC_NAME   = "translation.csv.enc";

    // ===== Public API =====

    public static string Translate(string s)
    {
        if (string.IsNullOrEmpty(s)) return s;
        EnsureLoaded();
        string key = Normalize(s);
        if (_map != null && _map.TryGetValue(key, out var t) && !string.IsNullOrEmpty(t))
            return t;
        return s;
    }

    public static string TranslateWithSubstring(string s)
    {
        if (string.IsNullOrEmpty(s)) return s;
        EnsureLoaded();

        var norm = Normalize(s);
        if (_partialCache.TryGetValue(norm, out var cached))
            return cached;

        var sb = new StringBuilder(norm.Length);
        int i = 0;
        bool any = false;
        while (i < norm.Length)
        {
            bool replaced = false;
            foreach (var pair in _subsDesc) // 긴 키 우선
            {
                var src = pair.src;
                if (src.Length == 0 || i + src.Length > norm.Length) continue;
                if (string.Compare(norm, i, src, 0, src.Length, StringComparison.Ordinal) == 0)
                {
                    sb.Append(pair.dst);
                    i += src.Length;
                    any = true;
                    replaced = true;
                    break;
                }
            }
            if (!replaced) { sb.Append(norm[i]); i++; }
        }

        var result = any ? sb.ToString() : s;
        _partialCache[norm] = result;
        return result;
    }

    public static string TranslateSmart(string s)
    {
        var exact = Translate(s);
        if (!ReferenceEquals(exact, s)) return exact;
        return TranslateWithSubstring(s);
    }

    // ===== Load / Decrypt =====

    private static void EnsureLoaded()
    {
        if (_loaded) return;
        _loaded = true;
        _map = new Dictionary<string, string>(StringComparer.Ordinal);

        try
        {
            string dir = Application.streamingAssetsPath;
            string plainPath = Path.Combine(dir, PLAIN_NAME);
            string encPath   = Path.Combine(dir, ENC_NAME);

            // 1) 평문 우선
            if (!File.Exists(plainPath))
            {
                // 2) .enc 복호화 → 평문 생성 시도
                if (File.Exists(encPath))
                {
                    if (TryDecryptEncToPlain(encPath, plainPath))
                    {
                        // 복호화 성공: 한 번 만들었으면 이후엔 평문만 사용
                    }
                }
            }

            if (File.Exists(plainPath))
            {
                foreach (string raw in File.ReadAllLines(plainPath, new UTF8Encoding(false)))
                {
                    if (string.IsNullOrWhiteSpace(raw)) continue;
                    if (raw.StartsWith("source,target", StringComparison.OrdinalIgnoreCase)) continue;

                    string[] parts = SplitCsv(raw);
                    if (parts.Length >= 2)
                    {
                        string src = UnescapeCsv(parts[0]);
                        string dst = UnescapeCsv(parts[1]);
                        src = Normalize(src);
                        dst = Normalize(dst);
                        if (!_map.ContainsKey(src))
                            _map[src] = dst;
                    }
                }
            }

            // 부분치환용 목록 준비(긴 키 우선)
            _subsDesc = new List<(string src, string dst)>(_map.Count);
            foreach (var kv in _map)
                if (!string.IsNullOrEmpty(kv.Key) && kv.Key != kv.Value)
                    _subsDesc.Add((kv.Key, kv.Value));
            _subsDesc.Sort((a, b) => b.src.Length.CompareTo(a.src.Length));
        }
        catch
        {
            // 조용히 무시
        }
    }

    private static bool TryDecryptEncToPlain(string encPath, string plainPath)
    {
        try
        {
            byte[] all = File.ReadAllBytes(encPath);
            if (all.Length < MAGIC.Length + 16 + 1) return false;

            for (int i = 0; i < MAGIC.Length; i++)
                if (all[i] != MAGIC[i]) return false;

            byte[] iv = new byte[16];
            Buffer.BlockCopy(all, MAGIC.Length, iv, 0, 16);
            int off = MAGIC.Length + 16;
            int ctLen = all.Length - off;
            if (ctLen <= 0 || (ctLen % 16) != 0) return false;

            byte[] ct = new byte[ctLen];
            Buffer.BlockCopy(all, off, ct, 0, ctLen);

            using var aes = Aes.Create();
            aes.Key = KEY;
            aes.IV = iv;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;

            using var ms = new MemoryStream();
            using (var cs = new CryptoStream(ms, aes.CreateDecryptor(), CryptoStreamMode.Write))
                cs.Write(ct, 0, ct.Length);
            var plain = ms.ToArray();

            Directory.CreateDirectory(Path.GetDirectoryName(plainPath) ?? ".");
            File.WriteAllBytes(plainPath, plain);
            return true;
        }
        catch
        {
            return false;
        }
    }

    // ===== CSV utils =====

    private static string[] SplitCsv(string line)
    {
        var res = new List<string>();
        bool inQ = false;
        var sb = new StringBuilder();
        for (int i = 0; i < line.Length; i++)
        {
            char c = line[i];
            if (inQ)
            {
                if (c == '"' && i + 1 < line.Length && line[i + 1] == '"') { sb.Append('"'); i++; }
                else if (c == '"') inQ = false;
                else sb.Append(c);
            }
            else if (c == ',')
            {
                res.Add(sb.ToString()); sb.Clear();
            }
            else if (c == '"')
            {
                inQ = true;
            }
            else
            {
                sb.Append(c);
            }
        }
        res.Add(sb.ToString());
        return res.ToArray();
    }

    private static string UnescapeCsv(string s)
    {
        s = s.Replace("\\\\", "\\")
             .Replace("\\r\\n", "\r\n")
             .Replace("\\n", "\n")
             .Replace("\\r", "\r")
             .Replace("\\t", "\t")
             .Replace("\\\"", "\"");
        return s;
    }

    private static string Normalize(string s)
        => s.Replace("\r\n", "\n").Replace("\r", "\n");

    // ===== State =====
    private static Dictionary<string, string> _map;
    private static bool _loaded;

    private static List<(string src, string dst)> _subsDesc = new List<(string src, string dst)>();
    private static readonly Dictionary<string, string> _partialCache = new Dictionary<string, string>(StringComparer.Ordinal);
}
