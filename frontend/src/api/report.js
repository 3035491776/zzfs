import request from './request'

export const reportApi = {
  monthly: (month) => request.get('/reports/monthly', { params: { month } }),
}
