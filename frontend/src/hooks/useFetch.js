import { useCallback, useEffect, useState } from "react";
import api, { errMsg } from "../services/api";

export default function useFetch(url, params, enabled = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState("");
  const key = JSON.stringify(params || {});

  const reload = useCallback(() => {
    if (!enabled) return Promise.resolve();
    setLoading(true);
    return api
      .get(url, { params })
      .then((r) => { setData(r.data); setError(""); })
      .catch((e) => setError(errMsg(e)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, key, enabled]);

  useEffect(() => { reload(); }, [reload]);
  return { data, loading, error, reload, setData };
}
