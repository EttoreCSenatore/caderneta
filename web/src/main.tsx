import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter} from 'react-router';
import {registerSW} from 'virtual:pwa-register';
import {App} from './App';
import {ApiError} from './lib/api';
import './styles.css';

const qc = new QueryClient({
  defaultOptions: {
    queries: {
      // 'always': sem internet a consulta roda mesmo assim e cai no que está guardado no aparelho (modo offline)
      networkMode: 'always',
      retry: (n, e) => !(e instanceof ApiError && e.status < 500) && n < 2,
      refetchOnWindowFocus: false,
    },
    mutations: {networkMode: 'always'},
  },
});

registerSW({immediate: true});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
