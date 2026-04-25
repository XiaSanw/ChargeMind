import axios from 'axios';
import type {
  ExtractRequest,
  ExtractResponse,
  EnrichResponse,
  DiagnoseResponse,
  StationProfile,
} from '@/types/diagnosis';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      throw new Error('请求超时，请检查后端服务是否启动');
    }
    if (error.response) {
      const { status, data } = error.response;
      switch (status) {
        case 422:
          throw new Error(data?.detail || '输入数据格式有误，请检查后重试');
        case 500:
          throw new Error('诊断服务暂时不可用，请稍后重试');
        case 503:
          throw new Error('LLM 服务限流，请等待 30 秒后重试');
        default:
          throw new Error(data?.detail || `服务异常 (${status})`);
      }
    }
    if (error.request) {
      throw new Error('无法连接服务器，请检查网络');
    }
    throw error;
  }
);

export const extractProfile = (userInput: string) =>
  apiClient.post<ExtractResponse>('/extract', { user_input: userInput } as ExtractRequest);

export const enrichProfile = (profile: StationProfile) =>
  apiClient.post<EnrichResponse>('/enrich', { profile });

export const diagnoseStation = (profile: StationProfile) =>
  apiClient.post<DiagnoseResponse>('/diagnose', { profile });

export default apiClient;
