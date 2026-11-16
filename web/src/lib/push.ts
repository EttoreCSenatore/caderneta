import {api} from './api';

export type ConfigPush = {ativo: boolean; chave_publica: string | null; permitido: boolean};

export const pushSuportado = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;

function chave(base64: string): Uint8Array<ArrayBuffer> {
  const pad = '='.repeat((4 - (base64.length % 4)) % 4);
  const bin = atob((base64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

/** Este aparelho já está inscrito? (o navegador guarda a inscrição; o servidor só o endereço) */
export async function inscricaoAtual(): Promise<PushSubscription | null> {
  if (!pushSuportado()) return null;
  const reg = await navigator.serviceWorker.ready;
  return reg.pushManager.getSubscription();
}

/** Pede permissão (só quando a pessoa clica) e registra este aparelho. */
export async function ativarPush(config: ConfigPush): Promise<void> {
  if (!config.chave_publica) throw new Error('O push não está ativado neste servidor.');
  const permissao = await Notification.requestPermission();
  if (permissao !== 'granted') throw new Error('A permissão de notificações foi negada no navegador.');
  const reg = await navigator.serviceWorker.ready;
  const sub = (await reg.pushManager.getSubscription()) ?? (await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: chave(config.chave_publica)}));
  await api('/push/inscricoes', {body: {endpoint: sub.endpoint}});
}

/** Cancela neste aparelho (servidor e navegador). Também é chamado ao sair do app. */
export async function desativarPush(): Promise<void> {
  const sub = await inscricaoAtual();
  if (!sub) return;
  try {
    await api('/push/cancelar', {body: {endpoint: sub.endpoint}});
  } finally {
    await sub.unsubscribe();
  }
}
