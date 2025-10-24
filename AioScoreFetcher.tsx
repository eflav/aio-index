import { useState } from "react";

export default function AioScoreFetcher() {
  const [url, setUrl] = useState("");
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sanitizeUrl = (input) => {
    return input
      .replace(/^https?:\/\//, "")
      .replace(/[\/\?\&\=\#]/g, "_")
      .replace(/_+$/, "");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setScore(null);

    const clean = sanitizeUrl(url);
    const jsonUrl = `https://eflav.github.io/aio-index/${clean}.json`;

    try {
      const res = await fetch(jsonUrl);
      if (!res.ok) throw new Error("Report not found yet. Try again soon.");
      const data = await res.json();
      setScore(data.data.aio_score || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 gap-4 text-center">
      <h2 className="text-2xl font-semibold">Check Your AIO Score</h2>
      <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-md">
        <input
          type="text"
          placeholder="Enter your website URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Go
        </button>
      </form>

      {loading && <p className="text-gray-500">Fetching AIO data...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {score !== null && !loading && (
        <div className="mt-4 text-4xl font-bold text-blue-600">
          {score}%
        </div>
      )}
    </div>
  );
}
