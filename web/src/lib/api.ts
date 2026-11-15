/** Cliente da API: mesma origem, cookie de sessão HttpOnly e cabeçalho anti-CSRF. */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

type Opts = {method?: string; body?: unknown; form?: FormData};

function mensagem(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) {
    const campo = detail[0].loc?.slice(-1)[0];
    return campo ? `${campo}: ${detail[0].msg}` : detail[0].msg;
  }
  return 'Algo deu errado. Tente novamente.';
}

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const headers: Record<string, string> = {'X-Caderneta': '1'};
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.body);
  }
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {method: opts.method ?? (body ? 'POST' : 'GET'), headers, body, credentials: 'same-origin'});
  } catch {
    throw new ApiError(0, 'Sem conexão. Verifique a internet.');
  }
  if (res.status === 204) return undefined as T;
  const data = res.headers.get('content-type')?.includes('json') ? await res.json() : await res.text();
  if (!res.ok) throw new ApiError(res.status, mensagem((data as {detail?: unknown})?.detail));
  return data as T;
}
