using System;
using System.IO;
using LibHac.Common;
using LibHac.Common.Keys;
using LibHac.Fs;
using LibHac.Fs.Fsa;
using LibHac.FsSystem;
using LibHac.Spl;
using LibHac.Tools.Fs;
using LibHac.Tools.FsSystem;
using LibHac.Tools.FsSystem.NcaUtils;

// Merged-RomFS extractor for Nobunaga's Ambition: Shinsei (Switch, JP).
// Applies the 1.1.4 update NCA as a BKTR patch over the base NCA and
// extracts the resulting merged RomFS (or exefs).
//
// SECURITY / LEGAL: this file intentionally does NOT contain any keys.
//   - Provide your own prod.keys (dumped from YOUR console) via PROD_KEYS.
//   - Provide the game's title keys (RightsId -> AccessKey) via TITLE_KEYS,
//     a title.keys file in the standard "rights_id=access_key" line format.
//   Do NOT commit prod.keys or title.keys anywhere. They are not distributed
//   with this project and are required to be sourced from your own dump.
//
// Env vars:
//   PROD_KEYS   path to prod.keys                     (required)
//   TITLE_KEYS  path to title.keys                    (required)
//   BASE_NCA    path to the base game data NCA        (required)
//   UPDATE_NCA  path to the 1.1.4 update data NCA     (required)
//   OUT_ROOT    output dir (default ./out)
//
// Usage:  dotnet run -c Release -- <list|extract [/PREFIX]|exefs>
class Program
{
    static string Env(string k, string def = null)
        => Environment.GetEnvironmentVariable(k) ?? def
           ?? throw new Exception($"environment variable {k} is required");

    static void Main(string[] args)
    {
        string prodKeys  = Env("PROD_KEYS");
        string titleKeys = Env("TITLE_KEYS");
        string baseNcaPath = Env("BASE_NCA");
        string updNcaPath  = Env("UPDATE_NCA");
        string outRoot = Env("OUT_ROOT", "out");

        // Loads prod.keys AND title.keys (title.keys supplies the RightsId->AccessKey
        // entries needed to decrypt title-key-crypto NCAs).
        var keySet = ExternalKeyReader.ReadKeyFile(prodKeys, titleKeys);

        var baseNca = new Nca(keySet, new LocalStorage(baseNcaPath, FileAccess.Read));
        var updNca  = new Nca(keySet, new LocalStorage(updNcaPath, FileAccess.Read));
        Console.WriteLine($"base title={baseNca.Header.TitleId:X}  update title={updNca.Header.TitleId:X}");

        IFileSystem romfs = updNca.OpenFileSystemWithPatch(baseNca, NcaSectionType.Data, IntegrityCheckLevel.None);

        string mode = args.Length > 0 ? args[0] : "list";
        if (mode == "exefs")
        {
            IFileSystem code = updNca.OpenFileSystemWithPatch(baseNca, NcaSectionType.Code, IntegrityCheckLevel.None);
            DumpFs(code, Path.Combine(outRoot, "exefs"), "*", "exefs");
            return;
        }
        if (mode == "list")
        {
            using var w = new StreamWriter(Path.Combine(outRoot, "merged_filelist.txt"));
            long n = 0;
            foreach (var e in romfs.EnumerateEntries("*", SearchOptions.RecurseSubdirectories))
                if (e.Type == DirectoryEntryType.File) { w.WriteLine($"{e.Size}\t{e.FullPath}"); n++; }
            Console.WriteLine($"merged romfs files: {n}");
        }
        else if (mode == "extract")
        {
            string prefix = args.Length > 1 ? args[1] : "/";
            DumpFs(romfs, outRoot, "*", "romfs", prefix);
        }
    }

    static void DumpFs(IFileSystem fs, string outRoot, string pattern, string tag, string prefix = "/")
    {
        int matched = 0;
        foreach (var e in fs.EnumerateEntries(pattern, SearchOptions.RecurseSubdirectories))
        {
            if (e.Type != DirectoryEntryType.File) continue;
            if (!e.FullPath.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) continue;
            matched++;
            string dst = outRoot + e.FullPath.Replace('/', Path.DirectorySeparatorChar);
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            using var uf = new UniqueRef<IFile>();
            fs.OpenFile(ref uf.Ref(), e.FullPath.ToU8Span(), OpenMode.Read).ThrowIfFailure();
            uf.Get.GetSize(out long sz).ThrowIfFailure();
            using var os = File.Create(dst);
            byte[] buf = new byte[1 << 20];
            long off = 0;
            while (off < sz)
            {
                uf.Get.Read(out long read, off, buf, ReadOption.None).ThrowIfFailure();
                if (read == 0) break;
                os.Write(buf, 0, (int)read); off += read;
            }
            Console.WriteLine($"{tag}: {e.FullPath} ({sz})");
        }
        Console.WriteLine($"matched {matched} files");
    }
}
