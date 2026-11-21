import {afterEach, describe, expect, it, vi} from 'vitest';
import {api, ApiError} from './api';

function resposta(status: number, corpo?: unknown) {
  const json = corpo !== undefined && typeof corpo !== 'string';
  return new Response(corpo === undefined ? null : json ? JSON.stringify(corpo) : (corpo as string), {
    status,
    headers: json ? {'content-type': 'application/json'} : {'content-type': 'text/plain'},
  });
}

afterEach(() => vi.unstubAllGlobals());

describe('cliente da API', () => {
  it('manda o cabeçalho anti-CSRF e o cookie da mesma origem', async () => {
    const f = vi.fn().mockResolvedValue(resposta(200, {ok: true}));
    vi.stubGlobal('fetch', f);
    expect(await api('/saude')).toEqual({ok: true});
    const [url, init] = f.mock.calls[0];
    expect(url).toBe('/api/saude');
    expect(init.method).toBe('GET');
    expect(init.headers['X-Caderneta']).toBe('1');
    expect(init.credentials).toBe('same-origin');
  });
  it('corpo vira POST com JSON; método explícito é respeitado', async () => {
    const f = vi.fn().mockResolvedValue(resposta(204));
    vi.stubGlobal('fetch', f);
    expect(await api('/x', {body: {a: 1}})).toBeUndefined();
    expect(f.mock.calls[0][1]).toMatchObject({method: 'POST', body: '{"a":1}'});
    expect(f.mock.calls[0][1].headers['Content-Type']).toBe('application/json');
    await api('/x', {method: 'DELETE'});
    expect(f.mock.calls[1][1].method).toBe('DELETE');
  });
  it('transforma erros da API em mensagens legíveis', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(resposta(403, {detail: 'Sem permissão para esta ação.'})));
    await expect(api('/x')).rejects.toMatchObject({status: 403, message: 'Sem permissão para esta ação.'});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(resposta(422, {detail: [{loc: ['body', 'email'], msg: 'inválido'}]})));
    await expect(api('/x')).rejects.toMatchObject({status: 422, message: 'email: inválido'});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(resposta(500, 'erro interno')));
    await expect(api('/x')).rejects.toMatchObject({status: 500, message: 'Algo deu errado. Tente novamente.'});
  });
  it('sem rede vira status 0 (o modo offline usa isso)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    const e = await api('/x').catch((x: unknown) => x);
    expect(e).toBeInstanceOf(ApiError);
    expect((e as ApiError).status).toBe(0);
  });
});
