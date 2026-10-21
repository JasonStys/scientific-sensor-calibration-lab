// Weighted calibration kernel by Jason Stys. Main, Read, Fit, Empty, SelfTest and Point fields:
// docs/CODE_INDEX.md. Variables: known response standard uncertainties, centered weighted moments,
// coefficient covariance and chi-square. No files, devices, sockets, shell commands or plugins.
using System.Text;
using System.Text.Json;

namespace Calibration;

/// <summary>Fixed-unit point: reference milli-units, signal microvolts, positive standard uncertainty microvolts.</summary>
internal readonly record struct Point(int X, int Y, int U);

/// <summary>Bounded stdin/stdout worker; exact-rational Python independently verifies every fit field.</summary>
internal static class Program
{
    /// <summary>Read one bounded strict UTF-8 request or run native analytical contracts; errors fail closed.</summary>
    public static int Main(string[] args)
    {
        try
        {
            if (args.SequenceEqual(new[] { "--self-test" })) { SelfTest(); return 0; }
            if (args.Length != 0) throw new ArgumentException("No input arguments supported");
            using var stream = Console.OpenStandardInput();
            using var buffer = new MemoryStream();
            var chunk = new byte[4096];
            int count;
            while ((count = stream.Read(chunk)) > 0)
            {
                buffer.Write(chunk, 0, count);
                if (buffer.Length > 65536) throw new ArgumentException("Input too large");
            }
            var body = new UTF8Encoding(false, true).GetString(buffer.ToArray());
            Console.WriteLine(JsonSerializer.Serialize(Fit(Read(body))));
            return 0;
        }
        catch (Exception error) when (error is ArgumentException or JsonException or InvalidOperationException or OverflowException)
        {
            Console.Error.WriteLine("Invalid bounded calibration request");
            return 2;
        }
    }

    /// <summary>Require exact nonduplicated keys and bounded integral values; no permissive number coercion.</summary>
    internal static List<Point> Read(string body)
    {
        using var document = JsonDocument.Parse(body, new JsonDocumentOptions { MaxDepth = 8 });
        var root = document.RootElement;
        Keys(root, ["points"]);
        var points = root.GetProperty("points");
        if (points.ValueKind != JsonValueKind.Array || points.GetArrayLength() > 64) throw new ArgumentException("Point count");
        var result = new List<Point>();
        foreach (var row in points.EnumerateArray())
        {
            Keys(row, ["x_milli", "signal_uv", "u_uv"]);
            if (!row.GetProperty("x_milli").TryGetInt32(out int x) || Math.Abs((long)x) > 1000000 ||
                !row.GetProperty("signal_uv").TryGetInt32(out int y) || Math.Abs((long)y) > 10000000 ||
                !row.GetProperty("u_uv").TryGetInt32(out int u) || u < 1 || u > 100000)
                throw new ArgumentException("Point range/type");
            result.Add(new Point(x, y, u));
        }
        return result;
    }

    /// <summary>Reject unexpected or duplicate property names before reading a JSON object.</summary>
    private static void Keys(JsonElement element, string[] expected)
    {
        if (element.ValueKind != JsonValueKind.Object) throw new ArgumentException("Expected object");
        var names = element.EnumerateObject().Select(p => p.Name).ToArray();
        if (names.Length != expected.Length || !names.ToHashSet().SetEquals(expected)) throw new ArgumentException("Object keys");
    }

    /// <summary>Return unavailable values explicitly; absence of a usable model is not a zero-slope estimate.</summary>
    private static Dictionary<string, object?> Empty(string status, int n)
    {
        return new()
        {
            ["status"] = status,
            ["n"] = n,
            ["a"] = null,
            ["b"] = null,
            ["var_a"] = null,
            ["var_b"] = null,
            ["cov_ab"] = null,
            ["chi2_reduced"] = null,
            ["xmin"] = null,
            ["xmax"] = null
        };
    }

    /// <summary>Fit y=a+b*x using centered double moments and known independent response variances, not residual scaling.</summary>
    internal static Dictionary<string, object?> Fit(List<Point> points)
    {
        if (points.Count < 4) return Empty("insufficient-calibration", points.Count);
        double xmin = points.Min(p => p.X) / 1000.0, xmax = points.Max(p => p.X) / 1000.0;
        if (xmax - xmin < 1) return Empty("insufficient-span", points.Count);
        double weight = points.Sum(p => 1e6 / ((double)p.U * p.U));
        double meanX = points.Sum(p => (1e6 / ((double)p.U * p.U)) * (p.X / 1000.0)) / weight;
        double meanY = points.Sum(p => (1e6 / ((double)p.U * p.U)) * (p.Y / 1000.0)) / weight;
        double sxx = points.Sum(p => (1e6 / ((double)p.U * p.U)) * Math.Pow(p.X / 1000.0 - meanX, 2));
        double sxy = points.Sum(p => (1e6 / ((double)p.U * p.U)) * (p.X / 1000.0 - meanX) * (p.Y / 1000.0 - meanY));
        double b = sxy / sxx, a = meanY - b * meanX;
        if (Math.Abs(b) < 0.01) return Empty("noninvertible-fit", points.Count);
        double chi = points.Sum(p => Math.Pow((p.Y / 1000.0 - a - b * (p.X / 1000.0)) / (p.U / 1000.0), 2)) / (points.Count - 2);
        return new()
        {
            ["status"] = "ok",
            ["n"] = points.Count,
            ["a"] = a,
            ["b"] = b,
            ["var_a"] = 1 / weight + meanX * meanX / sxx,
            ["var_b"] = 1 / sxx,
            ["cov_ab"] = -meanX / sxx,
            ["chi2_reduced"] = chi,
            ["xmin"] = xmin,
            ["xmax"] = xmax
        };
    }

    /// <summary>Native analytical and parser contracts independent of the Python adapter; throw on any mismatch.</summary>
    private static void SelfTest()
    {
        var points = Enumerable.Range(0, 5).Select(i => new Point(i * 1000, 10000 + 2000 * i, 1000)).ToList();
        var fit = Fit(points);
        if (Math.Abs((double)fit["a"]! - 10) > 1e-12 || Math.Abs((double)fit["b"]! - 2) > 1e-12 ||
            Math.Abs((double)fit["var_b"]! - 0.1) > 1e-12 || Math.Abs((double)fit["var_a"]! - 0.6) > 1e-12 ||
            Math.Abs((double)fit["cov_ab"]! + 0.2) > 1e-12 || (double)fit["chi2_reduced"]! != 0)
            throw new InvalidOperationException("Analytical fit/covariance");
        var scaled = Fit(points.Select(p => p with { U = p.U * 2 }).ToList());
        if (Math.Abs((double)scaled["var_b"]! - 0.4) > 1e-12) throw new InvalidOperationException("Uncertainty scaling");
        if ((string)Fit([])["status"]! != "insufficient-calibration" ||
            (string)Fit(points.Select(p => p with { X = 0 }).ToList())["status"]! != "insufficient-span" ||
            (string)Fit(points.Select(p => p with { Y = 1000 }).ToList())["status"]! != "noninvertible-fit")
            throw new InvalidOperationException("Unavailable contracts");
        foreach (string body in new[] { "{", "[]", "{\"points\":[],\"points\":[]}", "{\"points\":[{\"x_milli\":1,\"signal_uv\":1,\"u_uv\":0}]}" })
        {
            bool rejected = false;
            try { Read(body); } catch (Exception e) when (e is JsonException or ArgumentException or InvalidOperationException) { rejected = true; }
            if (!rejected) throw new InvalidOperationException("Parser rejected-input contract");
        }
        Console.WriteLine("Native analytical coefficients, covariance, scaling, degenerate fits and strict parser contracts passed");
    }
}
