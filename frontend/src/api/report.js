import request from './request'

export const reportApi = {
  monthly: (month) => request.get('/reports/monthly', { params: { month } }),
  aiAnalysis: (month) => request.post('/reports/monthly/ai-analysis', { month }),
}
