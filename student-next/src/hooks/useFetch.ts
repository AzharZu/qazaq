import useSWR, { SWRConfiguration } from "swr";
import api from "@/lib/api";

const fetcher = (url: string) => api.get(url).then((res) => res.data);

export function useFetch<T = any>(url: string | null, config?: SWRConfiguration) {
  const swr = useSWR<T>(url, url ? fetcher : null, config);
  return {
    ...swr,
    data: swr.data as T | undefined,
  };
}

export default useFetch;
